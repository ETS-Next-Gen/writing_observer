'''
This file defines helpers for connecting to the server
via an ipython kernel.

Use `start()` to launch a new kernel instance.
'''
import IPython
import ipykernel.kernelapp
import ipykernel.ipkernel
import json
import logging
import os
import sys
import threading
import zmq
from traitlets.config import Config

# generic log file for seeing ipython output
logging.basicConfig(filename='ZMQ.log', encoding='utf-8', level=logging.DEBUG)


class LOKernel(ipykernel.ipkernel.IPythonKernel):
    def __init__(self, **kwargs):
        import dash
        super().__init__(**kwargs)
        # we can't capture print statements due to the system passing sysout
        # around but this code is still being ran.
        dash.jupyter_dash = dash.jupyter_dash.__init__()

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
        return super().do_execute(code, silent, store_history, user_expressions, allow_stdin, cell_id=cell_id)


def record_iopub_port(connection_file_path):
    # Read the connection file to get the iopub_port
    with open(connection_file_path, 'r') as f:
        connection_info = json.load(f)
    iopub_port = connection_info.get('iopub_port', None)
    return iopub_port


def start(kernel_only=False, connection_file=None, iopub_port=None):
    '''Kernels can start in two ways.
    1. A user starts up a kernel(a)/interactive shell(b) OR
    2. A Jupyter client starts a kernel
    We support 1.a and 2 right now.

    When the Jupyter client starts it passes in a
    connection file to tell the system how to set up.
    This is done with the `-f` flag. We intercept
    this file to get the `iopub_port` which we should
    later send to `lo_event`. For now, we just log
    the messages published.

    Roadblocks with #1:
    - We want to log interactions with the server. When
      starting `IPython.embed()`, we were unable to monitor
      the passed in `iopub_port`.

    Other roadblocks:
    - To initiate the kernel properly, you must be run
      `jupyter` from the `/learning_observer` directory.
      The same location that we normally start the server
      with `python learning_observer`. The `passwd.lo`
      file is read in based on your current working directory.
      Other files may also be read in this way. We just
      haven't found and fixed them all yet.
    - We ough to know how console flags are being read in
      by `kernelapp.launch_new_instance()`. If we pass
      conflicting flags to LO, unexpected errors may occur.
    '''
    connection_file_available = connection_file is not None
    # HACK fix this
    iopub = 12345 if iopub_port is not None else iopub_port
    if connection_file_available:
        iopub = record_iopub_port(connection_file)
    thread = threading.Thread(target=monitor_iopub, args=(iopub,))
    thread.start()
    if kernel_only and connection_file_available:
        ipykernel.kernelapp.launch_new_instance(kernel_class=LOKernel)
        return
    if kernel_only:
        c = Config()
        c.IPKernelApp.iopub_port = iopub_port
        IPython.embed_kernel(config=c)
        return
    # figure out how to just launch the console. Last time we did this
    # we couldn't record the contents of the iopub port.
    # we were using IPython with a Config file to specify the port #


def load_kernel_spec():
    '''Load the `learning_observer_kernel`. This will create the
    kernel is one does not already exist.

    TODO when do we run this code? This code needs to run before
    jupyter client tries to connect. Jupyter will NOT know about
    the LO kernel without this method running first. Should
    jupyter be its own set of requirements on the system?

    TODO copy in logo files
    '''
    current_script_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_script_path)
    kernel_spec = {
        'argv': [sys.executable, current_directory, '--lokernel', '1', '-f', '{connection_file}'],
        'display_name': 'Learning Observer Kernel',
        'language': 'python',
        'name': 'learning_observer_kernel'
    }

    dirname = os.path.join(sys.prefix, 'share', 'jupyter', 'kernels', kernel_spec['name'])
    kernel_file = os.path.join(dirname, 'kernel.json')
    # check if we should even make it
    if os.path.isfile(kernel_file):
        print('Kernel found!\nUsing the following kernel spec:')
        with open(kernel_file, 'r') as f:
            print(json.dumps(json.load(f), indent=2))
        return
    print('Kernel NOT found!\nCreating a default kernel spec:')
    print(json.dumps(kernel_spec, indent=2))
    os.mkdir(dirname)
    print(dirname)
    with open(kernel_file, 'w') as f:
        json.dump(kernel_spec, f, sort_keys=True)
    # We can also store logos in the same directory
    # under `logo-64x64.png` or `logo-32x32.png`


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
