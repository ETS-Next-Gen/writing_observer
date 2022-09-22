# Prototypes

Required packages
```bash
cd learning_observer/prototypes/dash-testing
pip install -r requirements.txt
# this will fail on the learning-observer-components, remove that part of the file and try again
pip install git+https://github.com/ArgLab/learning_observer_dash_components # these components are not published anywhere so manual install is necessary
mkdir data  # create a directory for the data (not shared through Git)
# add the data files to this location
```

Running. Since you'll need two servers running, you'll need two terminals.
```bash
cd learning_observer/prototypes/dash-testing
python aiohttp_server.py   # dash application
```

Navigate to [http://127.0.0.1:8080/dashboard](http://127.0.0.1:8050/dashboard) to see the working prototype.

The examples directory is for single-page dash apps that show how to do different things.
