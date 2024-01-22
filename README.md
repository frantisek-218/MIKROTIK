# Sentinel DynFW Client

This is a Python script that serves as a client for Turris Sentinel Dynamic Firewall (DynFW). It communicates with a Turris Sentinel server using ZeroMQ, fetches server certificates, and manages IP addresses in a MikroTik RouterOS device.


## Commands:

``` 
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Migrate commands:

``` 
flask db init
flask db migrate
flask db upgrade
```
## Tutoriál pro zprovoznění MikroTiku skrze VirtualBox:
  ```
  https://www.youtube.com/watch?v=0FStQTNAgi4
  ```

## API:
**http://127.0.0.1:5000/swagger/v1**


## Requirements
- `argparse`: For command-line argument parsing.
- `logging`: For logging.
- `os`: For working with the operating system (e.g., creating directories).
- `subprocess`: For running external processes.
- `sys`: Provides access to some elements of the Python interpreter.
- `re`: For working with regular expressions.
- `time`: For working with time.
- `urllib.request`: For working with HTTP requests.
- `msgpack`: For encoding and decoding data in MessagePack format.
- `zmq`: ZeroMQ for inter-process or inter-thread communication.
- `routeros_api`: For communicating with MikroTik RouterOS API.
- `zmq.auth`: Authentication mechanisms for ZeroMQ.
- `zmq.utils.monitor`: Tools for monitoring events in ZeroMQ.
- `queue`: For creating a FIFO queue.
- `threading`: For working with threads.



