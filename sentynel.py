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
import routeros_api
import zmq.auth
from zmq.utils.monitor import recv_monitor_message
import time
import queue   
import threading

logger = logging.getLogger("sentinel_dynfw_client")

ip4 = '192.168.0.222'

SERVER_CERT_URL = "https://repo.turris.cz/sentinel/dynfw.pub"
SERVER_CERT_PATH_DEFAULT = r"C:\Users\frant\Desktop\PROJEKTOS\MIKROTIK\var\run\dynfw.pub"
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

MISSING_UPDATE_CNT_LIMIT = 10000

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
        self.addresses = set()  # Track addresses

    def add_ip(self, ip):
        if self.regexp.fullmatch(ip):
            self.commands.append('add {} {}\n'.format(self.name, ip))
            self.addresses.add(ip)  # Track added address
        else:
            logger.warning("IP address skipped as it is not IPv4: %s", ip)

    def del_ip(self, ip):
        if ip in self.addresses:
            # Remove the IP address from the set
            self.addresses.remove(ip)
            try:
                # Create a connection to the RouterOS device
                connection = routeros_api.RouterOsApiPool(ip4, username='admin', password='admin', port=8728,
                                                          plaintext_login=True)
                api = connection.get_api()

                # Send the command to the RouterOS device to remove the address
                api.get_resource('/ip/firewall/address-list').call('remove', {
                    'address': ip.encode('utf-8'),  # Encode as bytes
                    'list': self.name.encode('utf-8')  # Encode as bytes
                })

                print(f"Removed IP {ip} from the address list")

            except routeros_api.exceptions.RouterOsApiCommunicationError as e:
                logger.error("Error removing address from the list: %s", str(e))
            finally:
                if connection:
                    connection.disconnect()
        else:
            logger.warning("IP address not found in the list: %s", ip)

    def delete_all_addresses(self):
        connection = routeros_api.RouterOsApiPool(ip4, username='admin', password='admin', port=8728,
                                                  plaintext_login=True)
        api = connection.get_api()
        list_queues = api.get_resource('/ip/firewall/address-list')

        pole = list_queues.get()
        for prvek in pole:
            print(prvek)
            list_queues.remove(id=prvek['id'])

            print(id)
        connection.disconnect()

        # otestovat rychlost zápisu cca 10K ip adress
        # mazání přes ID - otestovat 10K
        # Otestovat rychlost výpisu 10k záznamů

        connection.disconnect()
    def commit(self):
        try:
            # Create a connection to the RouterOS device
            connection = routeros_api.RouterOsApiPool(ip4, username='admin', password='admin', port=8728,
                                                      plaintext_login=True)
            api = connection.get_api()

            # Iterate over the commands and send them to the RouterOS device
            for cmd in self.commands:
                try:
                    parts = cmd.split()
                    if len(parts) == 3 and parts[0] in ['add', 'remove']:
                        ip_address = parts[2]
                        action = 'add' if parts[0] == 'add' else 'remove'

                        # Send the command to the RouterOS device
                        api.get_binary_resource('/ip/firewall/address-list').call(action, {
                            'address': ip_address.encode('utf-8'),  # Encode as bytes
                            'list': self.name.encode('utf-8')  # Encode as bytes
                        })
                except routeros_api.exceptions.RouterOsApiCommunicationError as e:
                    if "failure: already have such entry" in str(e):
                        logger.warning("Address already exists in the list: %s", cmd)
                    elif "failure: entry not found" in str(e):
                        logger.warning("Address not found in the list: %s", cmd)
                    else:
                        logger.error("Error modifying address list: %s", str(e))

            self.commands = []  # Reset commands

            print("Commit called. Sending commands to MikroTik firewall.")

        except (PermissionError, FileNotFoundError) as e:
            logger.critical("Can't run ipset command: %s.", str(e))
            print("Can't run ipset command: {}.".format(str(e)), file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            logger.warning("Error running ipset command: %s.", str(e))
        finally:
            if connection:
                connection.disconnect()

    def reset(self):
        self.commands.append('create {} hash:ip family inet hashsize 1024 maxelem 65536\n'.format(self.name))
        self.commands.append('flush {}\n'.format(self.name))
        self.addresses = set()  # Reset tracked addresses
    def get_addresses(self):
        return list(self.addresses)  # Return tracked addresses


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
                print("Moc messages v hajzlu nevim co delat")
                return False
            self.received_out_of_order.add(serial)
            return True

    def reset(self, serial):
        # reset serial - after list reload
        self.received_out_of_order = set()
        self.current_serial = serial


class DynfwList:
    def __init__(self, socket, dynfw_ipset_name, api):
        self.socket = socket
        self.serial = Serial(MISSING_UPDATE_CNT_LIMIT)
        self.ipset = Ipset(dynfw_ipset_name)
        self.socket.setsockopt(zmq.SUBSCRIBE, TOPIC_DYNFW_LIST.encode('utf-8'))
        self.api = api






    def handle_delta(self, msg):
        for key in REQUIRED_DELTA_KEYS:
            if key not in msg:
                raise InvalidMsgError("missing delta key {}".format(key))
        if not self.serial.update_ok(msg["serial"]):
            logger.debug("Serial out of order, skipping delta update")
            return
        if msg["delta"] == "positive":
            self.ipset.add_ip(msg["ip"])
            logger.debug("DELTA message: +%s, serial %d", msg["ip"], msg["serial"])
        elif msg["delta"] == "negative":
            self.remove_ips(msg["ip"])
            logger.debug("DELTA message: -%s, serial %d", msg["ip"], msg["serial"])
        self.ipset.commit()

    def remove_ips(self, ips_to_remove):
        list_resource = self.api.get_resource('/ip/firewall/address-list')
        ip_to_delete = ips_to_remove

        # Get the list of addresses from the RouterOS device
        address_list = list_resource.get()

        # Find the index of the IP address to delete
        index_to_delete = next((i for i, item in enumerate(address_list) if item['address'] == ip_to_delete), None)

        # If the IP address is found, proceed with removal
        if index_to_delete is not None:
            id_to_delete = address_list[index_to_delete]['id']
            list_resource.remove(id=id_to_delete)
            print(f"Removed IP {ip_to_delete} from the address list")
        else:
            logger.warning("IP address not found in the list: %s", ip_to_delete)

    def handle_list(self, msg):
        for key in REQUIRED_LIST_KEYS:
            if key not in msg:
                raise InvalidMsgError("missing list key {}".format(key))
        self.serial.reset(msg["serial"])
        self.ipset.delete_all_addresses()  # Delete all addresses before filling the list
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

        


def fetch_server_ip_addresses(cert_url):
    try:
        with urllib.request.urlopen(cert_url) as urlf:
            ip_addresses = urlf.read().decode('utf-8').split('\n')
        return ip_addresses
    except urllib.error.URLError as exc:
        logger.error("Unable to fetch server IP addresses: %s", exc.reason)
        return []

def main():
    args = parse_args()
    configure_logging(args.verbose)
    if args.renew:
        server_addresses = renew_server_certificate(args.cert_url, args.cert)

    context = zmq.Context()
    socket = create_zmq_socket(context, args.cert)
    socket.connect("tcp://{}:{}".format(args.server, args.port))
    wait_for_connection(socket)

    # Create a connection to the RouterOS device
    api_connection = routeros_api.RouterOsApiPool(ip4, username='admin', password='admin', port=8728,
                                                  plaintext_login=True)
    api = api_connection.get_api()

    dynfw_list = DynfwList(socket, args.ipset, api)

    server_addresses = []  # Initialize with an empty list

    # Set the maximum duration in seconds for update functions
    max_update_duration = 6000000000  # for example, 1 hour

    start_time = time.time()

    # Create and register the poller object
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    while True:
        elapsed_time = time.time() - start_time

        if elapsed_time >= max_update_duration:
            print(f"Max update duration ({max_update_duration} seconds) reached. Exiting the loop.")
            break

        socks = dict(poller.poll(100000))  # Timeout in milliseconds

        if socket in socks and socks[socket] == zmq.POLLIN:
            try:
                msg = socket.recv_multipart()
                topic, payload = parse_msg(msg)
                if topic == TOPIC_DYNFW_LIST:
                    dynfw_list.handle_list(payload)
                    server_addresses = payload.get('list', [])
                elif topic == TOPIC_DYNFW_DELTA:
                    dynfw_list.handle_delta(payload)
                else:
                    logger.warning("Unknown message topic: %s", topic)

                # Update elapsed time only during the execution of update functions
                elapsed_time = time.time() - start_time
            except InvalidMsgError as e:
                logger.warning("Invalid message received: %s", e)
        else:
            print("No message received within the timeout.")

    # ... (any additional cleanup or actions if needed)

if __name__ == "__main__":
    main()





