# Learning Observer Workshop

This document will step you through the Learning Observer workshop. Our goals for this workshop are: 

* Give an overview of the platform
* Collect feedback on how to make the platform useful for your own work
* Collect feedback on different major components of the platform
* Have fun hacking learning analytics together

We recommend working in groups of three. This way:

* You can help each other
* At least one person will (hopefully) have a working machine

We suggest having at least 2 terminals ready for this workshop. The first terminal will be for installing and running the system, while the second will be any additional scripts to need to run.

Prerequisites:

* Unix-style system (Ubuntu is most tested, but MacOS and WSL should both work)
* `python 3`. We tested and recommend 3.10, but anything newer than 3.9 should work

Recommendations:

* `virtualenvwrapper`. If you prefer a different package management system, you can use that instead.
* `redis`. We need a key-value store. However, if you don't have this, we can use files on the file system or in-memory. If you use `docker compose`, it will spin this up for you.

Options:

* `docker`. We're not big fans of `docker` for this type of work, so this pathway is less tested. However, by popularity, we do provide a `docker` option. We tested with docker 26.1. You should only use this if you're fluent in `docker`, since you'll probably need to tweak instructions slightly (especially if you're not on 26.1).

If you'd like to use `docker`, we have a quick [docker.md](tutorial).

If you can install the prerequisites before the workshop, it will save a lot of time, and not put us at risk of issues due to hotel bandwidth.

We have a document with a more in-depth overview of the [technologies.md](technologies) we use.

### Python environment

We recommend working in a Python environment of some sort. Our preferred tool is [virtualenvwrapper](https://pypi.org/project/virtualenvwrapper/). You are welcome to use your own (`anaconda`, or as you prefer), but the steps are:

1) Install `virtualenvwrapper` (e.g. `pip install virtualenvwrapper`, `apt-get install python3-virtualenvwrapper`, etc.)

2) Run it:

```bash
export WORKON_HOME=$HOME/.virtualenvs
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
. /usr/share/virtualenvwrapper/virtualenvwrapper.sh
```

(Most people have the above in their `.bashrc`)

## Download

First make sure you clone the repository:

```bash
git clone https://github.com/ETS-Next-Gen/writing_observer.git lo_workshop
cd lo_workshop/
git checkout berickson/workshop # TODO remove this when this branch gets merged in
```

If you have a github account set up with ssh keys (you should!):
`git clone git@github.com:ETS-Next-Gen/writing_observer.git lo_workshop`
instead

NOTE: All future commands should be ran starting from the repository's root directory. The command will specify if changing directories is needed.

## Local environment

Make sure you are on a fresh virtual environment (e.g. `mkvirtualenv lo_workshop`), then run the install command:

```bash
make install
```

## Configuration

Before starting the system, let's take care of any extra configuration steps. We are currently in the process of moving configuration formats from YAML to [PMSS](https://github.com/ETS-Next-Gen/pmss).

We may discuss this in the workshop later, but for now, we will configure using YAML.

### creds.yaml

The `creds.yaml` is the primary configuration file on the system. The platform will not launch unless this file is present. Create a copy of the example in `learning_observer/learning_observer/creds.yaml.example`. We will copy this over, and then set up the pieces needed for the system to work.

You're welcome to run the `learning observer` between changes. In most cases, it will tell you exactly what needs to be fixed.

```bash
cp learning_observer/learning_observer/creds.yaml.example learning_observer/creds.yaml
```

Edit this file (e.g. `emacs learning_observer/creds.yaml`).

#### User Authentication

As a research platform, the Learning Observer supports many authentication schemes, since it's designed for anything from small cognitive labs and user studies (with no log-in) to large-scale school deployments (e.g. integrating with Google Classroom). This is pluggable.

For this workshop, we will disable Google authentication, and set the system up so we can use it with with no authentication:

```yaml
auth:
    # remove google_oauth from auth
    # google_oauth: ...

    # enable passwordless insecure log-ins
    # useful for quickly seeing the system up and running
    test_case_insecure: true
```

#### Event authentication

Learning event authentication is seperate from user authentication. We also have multiple schemes for this, but for testing and development, we will run without authentication.

```
# Allow all incoming events
event_auth:
    # ...
    testcase_auth: {}
```

#### Session management

Session management requires a unique key for the system. Type in anything (just make it complex enough):

```
# update session information
aio:
    session_secret: asupersecretsessionkeychosenbyyou
    session_max_age: 3600
```

Pro tip: If you start the system missing a command like this, it will usually tell you what's wrong and how to fix it (in the above case, generating a secure GUID to use as your session secret).

#### KVS

```
# If you are using Docker compose, you should change the redis host to
redis_connection:
  redis_host: redis
  redis_port: 6379
```

### admins.yaml & teachers.yaml

The platform expects both of these files to exist under `learning_observer/learning_observer/static_data/`. If these are missing on start-up, the platform create them for you and exit. Normally these are populated with the allowed Admins/Teachers for the system.

### passwd.lo

Each install of the system needs an admin password file associated with it. The `learning_observer/util/lo_passwd.py` file can be used to generate this password file. This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.

```bash
cd learning_observer/
python util/lo_passwd.py --username admin --password supersecureadminpassword --filename passwd.lo
```

Depending on how the `creds.yaml` authorization settings are configured, you may be required to use the password you create.

## Test the system

To run the system, use the run command

```bash
make run
```

## Build your own module

### Create from template

We provide a cookiecutter template for creating new modules for the Learning Observer. If you are using Docker, just create a local virtual environment to run this command. To create one run,

```bash
pip install cookiecutter
cd modules/
cookiecutter lo_template_module/
```

Cookiecutter will prompt you for naming information and create a new module in the `modules/` directory. By default, this is called `learning_observer_template`, but pick your own name and substitute it into the commands below. 

### Installing

To install the newly created project, use `pip` like any other Python package.

```bash
pip install -e modules/learning_observer_template/
```

If you are running the system with Docker and doing development, you should add the module install to the `make run` command.

```Makefile
run:
    pip install -e learning_observer/
    pip install -e modules/learning_observer_template/
    cd learning_observer && python learning_observer --watchdog=restart
```

## Streaming Data

We can stream data into the system to simulate a classroom of students working. Once the system is up and running, run
    
```bash
python learning_observer/util/stream_writing --fake-name --url=localhost:8888 --streams=10
```

This will generate events for 10 students typing a set of loremipsum texts and send them to `localhost:8888`.

This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.
