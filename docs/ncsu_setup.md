# NCSU system setup guide
# ==================================================

Currently the system is set for use with RHEL 8 on the NCSU systems.  We are running with Python 3.9 and connected to the AWEWorkbench code.  This assumes that we are also installing it into a vm with those tools installed as packages.  An installation script has been added to the servermanagement directory.  


Ihnstallation on RHEL 8 requires:

- python 3.9 or 3.10 (39 still default).
- redis.x86_64        5.0.3-5.module+el8.4.0+12927+b9845322    @rhel-8-for-x86_64-appstream-rpms   
- redis-devel.x86_64  5.0.3-5.module+el8.4.0+12927+b9845322    @rhel-8-for-x86_64-appstream-rpms




# Older RHEL 7 Notes.
# ==================================================


The following is a guide to help with the installation of Learning Observer (LO) on NCSU systems.

This guide assumes you are using an RHEL system.
Additionally, depending on where on the system you place the repository, you may need to run all commands as a sudo user.

## Requirements

LO is confirmed to work on `Python 3.8`.
Along with the base install of Python, LO requires the Python developer tools.
These can be installed with the following commands:

```bash
sudo yum install rh-python38    # base python
sudo yum install python38-devel # developer tools for python 3.8
```

On RHEL 7, the `python38-devel` is no longer recognized as a package.
To properly fetch the developer tools, use the following:

```bash
sudo subscription-manager repos --enable rhel-7-server-optional-rpms --enable rhel-server-rhscl-7-rpms
sudo yum install rh-python38-python-devel.x86_64
```

The Python installation should be located at `/opt/rh/rh-python38`.
Note this location for future sections.

There is a chance you'll encounter an issue when installing the requirements, specifically `py-bcrypt`.
The developer tools do not show up in the exact proper place, so we need to create a soft symbolic link between the correct location and where they are located.
To create this link, use the following:

```bash
cd /opt/rh/rh-python38/root
sudo ln -s usr/include/ .  # check that Python.h exists in usr/include/python3.8/Python.h
```

Note, we are creating a link between the subdirectory `/opt/rh/rh-python38/root/usr/include` and `/opt/rh/rh-python38/root`.
Using `/usr/include` will result in the incorrect link.

## Install

### Virtual Environment

To make sure we are using the proper installation of Python, we will use a virtual environment.
To do this, run the following command:

```bash
/path/to/python3.8/ -m venv /path/of/desired/virtual/environment
```

Again, keep note of where the virtual environment is located for future steps.

### Config files

For each system, you'll need to create a new `creds.yaml` file within the `/path/to/repo/learning_observer` directory.
This file defines what type of connections are allowed to be made to the system.
Luckily, there is an example file you can copy located in the `/path/to/repo/learning_observer/learning_observer` directory.
When attempting to run the system later on in this setup guide, if you have any misconfigured here, then the system will tell you what's wrong.

Some of the main changes that need to be made are:

1. types of `auth` allowed, for simple setup, just remove the `google` child and all its subchildren
1. `aio` session secret and max age
1. `event_auth` to allow access from various locations (like Chromebooks)
1. `server` for reconfiguring the port information
1. `config:logging` for determining the `max_size` (in bytes) of each log file and total `backups` to keep around before rotating.

More configurables are expected to be included in this config file in the future.

### Package installation

Before we get started installing packages, we must ensure that the `pip` in our virtual environment is up to date.
Some of the packages located in the `requirements.txt` file require `wheel` to be installed first.
After the base requirements are installed, we will also need to install the local packages (the Writing Observer module and the Learning Observer module).
To handle all the installs, use the following:

```bash
cd writing_observer                                         # cd into the top level of the repository
/path/to/venv/bin/pip install --upgrade pip                 # upgrade pip
/path/to/venv/bin/pip install wheel                         # install wheel
/path/to/venv/bin/pip install -r requirements.txt           # install package requirements
/path/to/venv/bin/pip install -e learning_observer/         # install learning observer module
/path/to/venv/bin/pip install -e modules/writing_observer/  # install writing observer module
```

### Needed directories

When installing Learning Observer for the first time, we need to create a few directories.
Use the following commands:

```bash
mkdir /path/to/repo/learning_observer/learning_observer/static_data/course_lists
mkdir /path/to/repo/learning_observer/learning_observer/static_data/course_rosters
mkdir /path/to/repo/learning_observer/learning_observer/logs
mkdir /path/to/repo/learning_observer/learning_observer/logs/startup
```

### Proxy server

By default, LO runs on port 8888.
Configure nginx, or another proxy server, for LO's port.

### Executable files

If this is the first time you are running the server on your system, you might need to make the shell scripts in the `servermanagement` directory executable.
To do this, use the following commands

```bash
chmod +x /path/to/repo/servermanagement/RunLearningObserver.sh
chmod +x /path/to/repo/servermanagement/BackupWebSocketLogs.sh
```

## System specific changes

There are various lines of code that point to specific servers.
For each setup, we need to make sure these are pointing to the proper place.

### Server

#### Auth information

On the server, we need to point the redirect uri to the server we are working with.
Depending on how the credentials files was handled, this change may not be necessary to get the system running.
The redirect uri is used with the Google login.
If that is not used, then this step is not needed.
This is located in `/path/to/repo/learning_observer/learning_observer/auth/social_sso.py`.

#### Server management

Additionally, we need to set up the server management files in the `/path/to/repo/servermanagement` direcotry.

In the `RunLearningObserver.sh` file, you'll want to set the system variables to match the current system.

```bash
VIRTUALENV_PYTHON="/full/path/to/venv/bin/pip"
LEARNING_OBSERVER_LOC="/full/path/to/repo/learning_observer"
LOGFILE_DEST="/path/to/log/storage"
```

In the `BackupWebsocketLogs.sh` file, you'll want to set log directory to the same place as you set in `RunLearningObserver.sh` and set where the logs should be backed up.

```bash
LOGFILE_SRC="/path/to/log/storage"
LOGFILE_DEST="/path/to/log/backups"
```

### Client

On the clientside, we need to add the correct server to  the `websocket_logger()` method in the `/path/to/repo/extension/extension/background.js` file.
If the server has SSL enabled, then the address we add should start with `wss://`.
If SSL is not enabled, then the address should start with `ws://`.
If a proxy server is not setup yet, make sure to include the port number (default 8888) on the end of the address.
An example of each instance is shown below:

```js
websocket_logger("wss://writing.csc.ncsu.edu/wsapi/in/")        // SSL enabled, nginx set
websocket_logger("ws://writing.csc.ncsu.edu:8888/wsapi/in/")    // SSL not enabled, nginx not setup 
```

## Running the server

There are 2 different ways we can run the system.
One is better for debugging, whereas the other is best for when you want to run the server and leave it up.
We suggest completely testing the installation with the debugging steps first.

### For debugging

To run the system for debugging, we will just run the Learning Observer module.
This will output all the log information to the console.
To do this, use the following command:

```bash
/path/to/venv/bin/python /learning_observer/learning_observer/  # run the learning observer module from within the learning observer directory
```

You should see any errors printed directly to the console.

### As a server

To run the system as a server, we will run the `RunLearningObserver.sh` script.
This fetches the virtual environment, runs the server, and pipes files into the proper log location we setup during the **System specific changes** section.
Run the following commands:

```bash
./servermanagement/RunLearningObserver.sh
```

Check the logs for any errors.

## Connecting the client

The client is run through a Google Chrome extension.
To properly use the client, you must sign into Chrome and use the same account to access to Google Docs.

From there, navigate to the extension manage located in settings.
Turn on Developer Mode (top right), then click the `Load Unpacked` button.
This opens a file explorer, where you should locate the repository.
More specifically, select the `writing_observer/extension/extension` directory.
This will unpack the extension and make it available for use in Google Chrome.

To make sure it is working, click on the `background page` link on extension card from within the extension manager.
This opens an inspect window.
On this window, select the `Console` tab.
Next, open a Google doc and start typing.
You should see events within the console.
Ensure there are no logs sprinkled in.

## Backing up logs

Whenever a websocket is made, the server creates a new log file for that connection on top of the primary logs files.
We need to backup both the generic log files as well as all the websocket specific logs.

### General logs

The main logger for events is located in `event_logger.json`.
This is automatically backed up via the built-in Python logging module.
The settings for this file are handling via the `creds.yaml` file that you previously setup.
Simply changing the values and restarting the server will update the logging procress.

### Websocket logs

The websocket logs take a little more setting up.
We will set up a daily `cron` job to run a backup script, `/path/to/repo/servermanagement/BackupWebsocketLogs.sh`.
The backup script will search the log directory for any logs that match the websocket pattern and were last modified in the last **60 minutes**.
Next, the backup script will remove any files that match the pattern and were modifed in the last **120 minutes**.

To set up the cron job, we first enter the crontab utility then add a line for the backup script.

```bash
crontab -e  # open the cron job menu

0 1 * * * /usr/bin/sh /full/path/to/repo/servermanagement/BackupWebsocketLogs.sh # line to add to the cronjob
# Run it at the 0th minute every hour, every day, every month, and so on
```




# Usage Notes
# =================================================================
# Instructions for Configuring Writing Observer on RHEL Installations
### Install Global Dependencies
1. sudo yum install redis
2. sudo yum install git
3. sudo yum install nginx

## Install Required RH Python 3.8
4. sudo subscription-manager repos --enable rhel-7-server-optional-rpms \
  --enable rhel-server-rhscl-7-rpms
5. sudo yum -y install @development
6. sudo yum -y install rh-python38

* rh-pyhon38 dev tools are also required

## Setup RH Python 38 and Virtual Envs
7. scl enable rh-python38 bash
8. python --version
* The output should indicate that python 3.8 is active
9. sudo pip install virtualenvwrapper
10. sudo source `/opt/rh/rh-python38/root/usr/local/bin/virtualenvwrapper.sh`
  
## Install Local Dependencies 
11. sudo git clone `https://github.com/ArgLab/writing_observer`
12. cd writing_observer
13. make install
14. sudo mkvirtualenv learning_observer
15. pip install -r requirements.txt
16. cd learning_observer
17. python setup.py develop
18. python learning_observer

* At this point, follow the system's further instructions until the process runs on port 8888 by default

## Server Setup
19. Populate creds.yaml with required Google Cloud Parameters
20. Configure nginx on `port 80` as a proxy for Learning Observer on `port 8888`
21. Replace all instances of `writing.csc.ncsu.edu` with custom server address in all files in directory `~/writing_observer/learning_observer/learning_observer/auth`

## Client/Extension Setup
22. Replace all instances of `writing.csc.ncsu.edu` with custom server address in `~/writing_observer/extension/background.js`
* If SSL is not enabled for the server, all websocket protocols should begin with `ws://` as opposed to `wss://`
23. Open Chrome and navigate to `chrome://extensions`
24. Click on "Load Unpacked". Select `~/writing_observer/extensions` and ensure that it is enabled
25. Select `background page` on the extension section and ensure no errors are present
26. Open a Google Docs document while signed into Chrome and ensure websocket communication between client and server is active