'''
This file defines helpers for connecting to the server
via an ipython kernel.

Use `start()` to launch a new kernel instance.
'''
from aiohttp import web
import asyncio
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


async def start_server(runner):
    await runner.setup()
    # TODO set this to the correct port
    site = web.TCPSite(runner, 'localhost', 9999)
    await site.start()


def record_iopub_port(connection_file_path):
    # Read the connection file to get the iopub_port
    with open(connection_file_path, 'r') as f:
        connection_info = json.load(f)
    iopub_port = connection_info.get('iopub_port', None)
    return iopub_port


def start(kernel_only=False, connection_file=None, iopub_port=None, lo_app=None):
    '''Kernels can start in two ways.
    1. A user starts up a kernel OR
    2. A user starts up an interactive shell OR
    3. A Jupyter client (lab/notebook) starts a kernel
    We support 1 and 3 right now.

    When the Jupyter client starts it passes in a
    connection file to tell the system how to set up.
    This is done with the `-f` flag. We intercept
    this file to get the `iopub_port`. We log messages
    published on this port.

    Roadblocks:
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

    # HACK The reason for nesting is including the
    # `lo_app` in the initialization. Spent a small
    # amount of time trying to pass in arguments to
    # the LOKernel constructor, but did not find
    # initial success. Worth trying again later.
    class LOKernel(ipykernel.ipkernel.IPythonKernel):
        '''Intercept the Kernel to fix any issues with
        in the startup configuration and to start the
        learning observer platform alongside.
        '''
        def __init__(self, **kwargs):
            import dash
            super().__init__(**kwargs)
            dash.jupyter_dash = dash.jupyter_dash.__init__()
            self.lo_runner = web.AppRunner(lo_app)

        def start(self):
            super().start()
            # TODO should starting the LO platform alongside
            # the kernel be the default?
            asyncio.run_coroutine_threadsafe(start_server(self.lo_runner), self.io_loop.asyncio_loop)

        def do_shutdown(self, restart):
            asyncio.run_coroutine_threadsafe(self.lo_runner.cleanup(), self.io_loop.asyncio_loop)
            return super().do_shutdown(restart)

        def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
            '''This method handles execution of code cells.
            If there is code to be run with all cells, it should be placed here.
            '''
            return super().do_execute(code, silent, store_history, user_expressions, allow_stdin, cell_id=cell_id)

    connection_file_available = connection_file is not None

    # Start the listener in a separate thread
    # HACK fix this - should this just be a setting?
    iopub = 12345 if iopub_port is None else iopub_port
    if connection_file_available:
        iopub = record_iopub_port(connection_file)
    thread = threading.Thread(target=monitor_iopub, args=(iopub,))
    thread.start()

    if kernel_only and connection_file_available:
        ipykernel.kernelapp.launch_new_instance(kernel_class=LOKernel)
        return
    if kernel_only:
        c = Config()
        c.IPKernelApp.iopub_port = iopub
        IPython.embed_kernel(config=c, kernel_class=LOKernel)
        return
    # TODO serve an interactive shell
    # We want to log interactions with the server. When
    # starting `IPython.embed()`, the recommended way
    # to start an interactive shell, we were unable to monitor
    # messages passed on the `iopub_port`.
    # BUG the IOPub monitor thread is still running so this
    # will not exit the python script
    raise NotImplementedError('Serving only an interactive shell has not yet been implemented.')


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
        # downstream arg parsers in the `ipykernel` do not like
        # empty parameters, which is why we pass `1`
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
    with open(kernel_file, 'w') as f:
        json.dump(kernel_spec, f, sort_keys=True)
    # We can also store logos in the same directory
    # under `logo-64x64.png` or `logo-32x32.png`


def monitor_iopub(port):
    '''Setup listener for the IO Pub ZMQ socket to
    listen for and log messages.

    Incoming messages are a list with the following items:

    ```python
    inc_msg = [
        b'kernel.<id>.<msg_type>',  # ZMQ routing prefix
        b'<IDS|MSG>',               # Delimeter key (always the same)
        b'some-cryptographic-str',  # HMAC string for authentication
        b'{"msg_id": "", ...}'      # message contents
    ]
    ```

    Jupyter recommends using `jupyter_client.session.Session` for
    consuming messages sent back and forth. Perhaps the next
    iteration of this code should look into that.
    '''
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f'tcp://localhost:{port}')
    topic_filter = b''
    subscriber.setsockopt(zmq.SUBSCRIBE, topic_filter)

    # message types we want to record
    logged_msg_types = ['execute_input', 'execute_result']
    try:
        while True:
            message = subscriber.recv_multipart()
            # TODO only log the types of messages we want to see
            # there are 2 different ways to fetch the message type
            # msg_type = message[0].decode().split('.')[-1]
            # msg_type = json.loads(message[3].decode())
            # if msg_type.get('msg_type', None) in logged_msg_types:
            if True:
                logging.debug(f"Received message: {message}")
    except zmq.ZMQError as e:
        logging.debug(f"Subscriber terminated due to error: {e}")
    finally:
        subscriber.close()
        context.term()
