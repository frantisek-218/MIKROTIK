#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
import re
import time
import urllib.request
import msgpack
import zmq
import zmq.auth
from zmq.utils.monitor import recv_monitor_message

logger = logging.getLogger("sentinel_dynfw_client")

SERVER_CERT_URL = "https://repo.turris.cz/sentinel/dynfw.pub"
SERVER_CERT_PATH_DEFAULT = "/var/run/dynfw_server.pub"
CLIENT_CERT_PATH = "./dynfw"

TOPIC_DYNFW_DELTA = "dynfw/delta"
TOPIC_DYNFW_LIST = "dynfw/list"

REQUIRED_DELTA_KEYS = (
    "serial",
    "delta",
    "ip",
)
REQUIRED_LIST_KEYS = (
    "serial",
    "list",
)

# Source: https://riptutorial.com/regex/example/14146/match-an-ip-address
RE_IPV4 = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

MISSING_UPDATE_CNT_LIMIT = 10


def renew_server_certificate(cert_url, cert_path):
    logger.info("Renewing server certificate")
    delay = 1
    while True:
        try:
            with urllib.request.urlopen(cert_url) as urlf:
                with open(cert_path, "wb") as filef:
                    filef.write(urlf.read())
            return
        except urllib.error.URLError as exc:
            delay = delay * 2 if delay < 120 else delay  # At maximum we wait for two minutes to try again
            logger.warning("Unable to renew certificate (another try after %d sec): %s", delay, exc.reason)
            time.sleep(delay)
    logger.info("Server certificate renewed")


def wait_for_connection(socket):
    monitor = socket.get_monitor_socket()
    logger.debug("waiting for connection")
    while monitor.poll():
        evt = recv_monitor_message(monitor)
        if evt['event'] == zmq.EVENT_CONNECTED:
            logger.debug("connected")
            break
        if evt['event'] == 0x0800 or evt['event'] == 0x2000 or evt['event'] == 0x4000:
            # detect handshake failure
            # unfortunatelly, these constants are not yet in pyzmq
            # constants from https://github.com/zeromq/libzmq/blob/c8a1c4542d13b6492949e7525f4fe8da266cac2b/src/zmq_draft.h#L60
            # 0x0800 - ZMQ_EVENT_HANDSHAKE_FAILED_NO_DETAIL
            # 0x2000 - ZMQ_EVENT_HANDSHAKE_FAILED_PROTOCOL
            # 0x4000 - ZMQ_EVENT_HANDSHAKE_FAILED_AUTH
            logger.error("Can't connect - handshake failed.")
            print("Can't connect - handshake failed.", file=sys.stderr)
            sys.exit(1)
    socket.disable_monitor()
    monitor.close()


class Ipset:
    def __init__(self, name):
        self.name = name
        self.regexp = re.compile(RE_IPV4)
        self.commands = []

    def add_ip(self, ip):
        if self.regexp.fullmatch(ip):
            self.commands.append('add {} {}\n'.format(self.name, ip))
        else:
            logger.warning("IP address skipped as it is not IPv4: %s", ip)

    def del_ip(self, ip):
        if self.regexp.fullmatch(ip):
            self.commands.append('del {} {}\n'.format(self.name, ip))
        else:
            logger.warning("IP address removal skipped as it is not IPv4: %s", ip)

    def reset(self):
        self.commands.append('create {} hash:ip -exist\n'.format(self.name))
        self.commands.append('flush {}\n'.format(self.name))

    def commit(self):
        try:
            print(self.commands)
            #p = subprocess.Popen(['/usr/sbin/ipset', 'restore'], stdin=subprocess.PIPE)
            #for cmd in self.commands:
            #    p.stdin.write(cmd.encode('utf-8'))
            #p.stdin.close()
            #p.wait()
            self.commands = []
            #if p.returncode != 0:
            #    logger.warning("Error running ipset command: return code %d.", p.returncode)
        except (PermissionError, FileNotFoundError) as e:
            # these errors are permanent, i.e., they won't disappear upon next run
            logger.critical("Can't run ipset command: %s.", str(e))
            print("Can't run ipset command: {}.".format(str(e)), file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            # the rest of OSError should be temporary, e.g., ChildProcessError or BrokenPipeError
            logger.warning("Error running ipset command: %s.", str(e))


def create_zmq_socket(context, server_public_file):
    socket = context.socket(zmq.SUB)
    if not os.path.exists(CLIENT_CERT_PATH):
        os.mkdir(CLIENT_CERT_PATH, mode=0o770)
    _, client_secret_file = zmq.auth.create_certificates(CLIENT_CERT_PATH, "client")
    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    socket.curve_secretkey = client_secret
    socket.curve_publickey = client_public
    server_public, _ = zmq.auth.load_certificate(server_public_file)
    socket.curve_serverkey = server_public
    return socket


class InvalidMsgError(Exception):
    pass


def parse_msg(data):
    try:
        msg_type = str(data[0], encoding="UTF-8")
        payload = msgpack.unpackb(data[1], raw=False)
    except IndexError:
        raise InvalidMsgError("Not enough parts in message")
    except (TypeError, msgpack.exceptions.UnpackException, UnicodeDecodeError) as e:
        raise InvalidMsgError("Broken message: {}".format(e))
    return msg_type, payload


class Serial:
    def __init__(self, missing_limit):
        self.missing_limit = missing_limit
        self.received_out_of_order = set()
        self.current_serial = 0

    def update_ok(self, serial):
        # update serial & return bool
        # return whether the serial is ok or if the list should be reloaded
        if serial == self.current_serial + 1:
            # received expected serial
            self.current_serial = serial
            while self.current_serial + 1 in self.received_out_of_order:
                # rewind serials
                self.current_serial = self.current_serial + 1
                self.received_out_of_order.remove(self.current_serial)
            return True
        else:
            if serial < self.current_serial:
                logger.debug("received lower serial (restarted server?)")
                return False
            if len(self.received_out_of_order) > self.missing_limit:
                logger.debug("too many missed messages")
                return False
            self.received_out_of_order.add(serial)
            return True

    def reset(self, serial):
        # reset serial - after list reload
        self.received_out_of_order = set()
        self.current_serial = serial


class DynfwList:
    def __init__(self, socket, dynfw_ipset_name):
        self.socket = socket
        self.serial = Serial(MISSING_UPDATE_CNT_LIMIT)
        self.ipset = Ipset(dynfw_ipset_name)
        self.socket.setsockopt(zmq.SUBSCRIBE, TOPIC_DYNFW_LIST.encode('utf-8'))

    def handle_delta(self, msg):
        for key in REQUIRED_DELTA_KEYS:
            if key not in msg:
                raise InvalidMsgError("missing delta key {}".format(key))
        if not self.serial.update_ok(msg["serial"]):
            logger.debug("going to reload the whole list")
            self.socket.setsockopt(zmq.UNSUBSCRIBE, TOPIC_DYNFW_DELTA.encode('utf-8'))
            self.socket.setsockopt(zmq.SUBSCRIBE, TOPIC_DYNFW_LIST.encode('utf-8'))
            return
        if msg["delta"] == "positive":
            self.ipset.add_ip(msg["ip"])
            logger.debug("DELTA message: +%s, serial %d", msg["ip"], msg["serial"])
        elif msg["delta"] == "negative":
            self.ipset.del_ip(msg["ip"])
            logger.debug("DELTA message: -%s, serial %d", msg["ip"], msg["serial"])
        self.ipset.commit()

    def handle_list(self, msg):
        for key in REQUIRED_LIST_KEYS:
            if key not in msg:
                raise InvalidMsgError("missing list key {}".format(key))
        self.serial.reset(msg["serial"])
        self.ipset.reset()
        for ip in msg["list"]:
            self.ipset.add_ip(ip)
        self.ipset.commit()
        logger.debug("LIST message - %s addresses, serial %d", len(msg["list"]), msg["serial"])
        self.socket.setsockopt(zmq.UNSUBSCRIBE, TOPIC_DYNFW_LIST.encode('utf-8'))
        self.socket.setsockopt(zmq.SUBSCRIBE, TOPIC_DYNFW_DELTA.encode('utf-8'))


def parse_args():
    parser = argparse.ArgumentParser(description='Turris::Sentinel Dynamic Firewall Client')
    parser.add_argument('-s',
                        '--server',
                        default="sentinel.turris.cz",
                        help='Server address')
    parser.add_argument('-p',
                        '--port',
                        type=int,
                        default=7087,
                        help='Server port')
    parser.add_argument('-c',
                        '--cert',
                        default=SERVER_CERT_PATH_DEFAULT,
                        help='Path to file with server ZMQ certificate')
    parser.add_argument('-r',
                        '--renew',
                        action="store_true",
                        help='Renew or get Server ZMQ certificate')
    parser.add_argument('--cert-url',
                        default=SERVER_CERT_URL,
                        help='URL to receive server certificate from when --renew is used')
    parser.add_argument('--ipset',
                        default="turris-sn-dynfw-block",
                        help='IPset name to push blocked IPs to')
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        help='Increase output verbosity')
    return parser.parse_args()


def configure_logging(debug: bool):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)


def main():
    args = parse_args()
    configure_logging(args.verbose)

    if args.renew:
        renew_server_certificate(args.cert_url, args.cert)

    context = zmq.Context()
    socket = create_zmq_socket(context, args.cert)
    socket.connect("tcp://{}:{}".format(args.server, args.port))
    wait_for_connection(socket)
    dynfw_list = DynfwList(socket, args.ipset)
    while True:
        msg = socket.recv_multipart()
        try:
            topic, payload = parse_msg(msg)
            if topic == TOPIC_DYNFW_LIST:
                dynfw_list.handle_list(payload)
            elif topic == TOPIC_DYNFW_DELTA:
                dynfw_list.handle_delta(payload)
            else:
                logger.warning("received unknown topic: %s", topic)
        except InvalidMsgError as e:
            logger.error("Invalid message: %s", e)


if __name__ == "__main__":
    main()
