# Interactive Environments

The Learning Observer can launch itself in a variety of ways.
These include launching itself alongside an IPython kernel.
This allows for users to directly interact with the LO system.
Users can connect to the kernel through the command line or a Jupyter clients, such as Jupyter Lab or Jupyter Notebooks.
This is useful for debugging or rapidly prototyping within the system.
When starting a kernel, the normal aiohttp server is also served alongside it.

## Architechture

The IPython kernel handles various event loops for different commmunications that occur within itself.
These event loops could handle code requests from the user or shutdown requests from a system message.
The events are communicated using the [ZMQ Protocol](https://zeromq.org/).
There are 5 dedicated sockets for communications where events occur:

1. **Shell**: Requests for code execution from clients come in
1. **IOPub**: Broadcast channel which includes all side effects
1. **stdin**: Raw input from user
1. **Control**: Dedicated to shutdown and restart requests
1. **Heartbeat**: Ensure continuous connection

Upon startup, we create a separate thread to monitor and log events on the information rich IOPub socket.
Additionally, we use an [aiohttp runner](https://docs.aiohttp.org/en/stable/web_reference.html#running-applications) to serve the LO application through the internal `ipykernel.io_loop` [Tornado](https://www.tornadoweb.org/en/stable/) event loop.
The runner method attaches itself to the provided event loop instead of the normal running method which creates a new event loop.

## IPython Shell/Kernel

We can startup the server as an IPython interactive shell or as a kernel we can connect to.

```bash
# Start an interactive shell
python learning_observer/ --loconsole

# Start an ipython kernel
# note: the 1 is needed to make the ipython kernel instance we launch happy
python learning_observer/ --lokernel 1
# this will provide you a specific kernel json file to use
# Connect to the specified kernel
jupyter console --existing kernel-123456.json
```

## Jupyter Clients

### Connect with Jupyter

Jupyter clients have a set of directories it will look for kernels in.
We need to create the LO kernel files, so the client will be able to choose the LO kernel.
Running the LO platform once will automatically create the kernel file in the `/<virtual_env>/share/jupyter/kernels/` directory.

```bash
# run once to create the kernel file
python learning_observer/
# open jupyter client of your choice
jupyter lab
# select the LO kernel from the kernel dropdown
```

### Helpers

The system offers some helpers for working with the LO platform from a Jupyter client.
The `local_reducer.ipynb` is an example notebook where we create a simple `event_count` reducer and create a corresponding dashboard.
This notebook calls `jupyter_helpers.add_reducer_to_lo` which handles adding your created reducer to all relavant aspects of the system.
