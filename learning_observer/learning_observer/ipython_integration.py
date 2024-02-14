'''
This file defines helpers for connecting to the server
via an interactive shell or ipython kernel.

Use `start()` to enter a shell
'''
import IPython
import json
import logging
import threading
import zmq
from traitlets.config import Config

# generic log file for seeing ipython output
logging.basicConfig(filename='ZMQ.log', encoding='utf-8', level=logging.DEBUG)


def start(kernel_only=False, iopub_port=12345):
    c = Config()
    c.IPKernelApp.iopub_port = iopub_port
    thread = threading.Thread(target=monitor_iopub, args=(iopub_port,))
    thread.start()
    if kernel_only:
        print('Connect to this kernel using jupyter console')
        IPython.embed_kernel(config=c)
    else:
        # TODO the iopub monitor does not log messages when
        # calling the `embed()` method. The `IPKernelApp` is
        # not used with this method.
        IPython.embed(config=c)


def monitor_iopub(port):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f'tcp://localhost:{port}')
    topic_filter = b''
    subscriber.setsockopt(zmq.SUBSCRIBE, topic_filter)

    logged_msg_types = ['execute_input', 'execute_result']
    print('starting loop')
    try:
        while True:
            # Receive messages
            # TODO research the structure here.
            # Why do we receive multiple a list of things?
            # what do these things map to?
            message = subscriber.recv_multipart()
            msg_type = json.loads(message[3].decode())
            # if msg_type.get('msg_type', None) in logged_msg_types:
            logging.debug(f"Received message: {message}")
    except zmq.ZMQError as e:
        logging.debug(f"Subscriber terminated due to error: {e}")
    finally:
        subscriber.close()
        context.term()
