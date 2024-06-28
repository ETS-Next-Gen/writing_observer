# Workshop setup

This document will detail setting Learning Observer platform.

## Install

First make sure you clone the repository

```bash
git clone https://github.com/ETS-Next-Gen/writing_observer.git lo_workshop
cd lo_workshop/
git checkout berickson/workshop # TODO remove this when this branch gets merged in
```
(or with host keys, `git clone git@github.com:ETS-Next-Gen/writing_observer.git lo_workshop`) 

### Technologies

The Learning Observer is ran as a Python aiohttp web application. The primary database used alongside is Redis.

We have a few additional Python scripts to run outside of the application. These are for setting up new modules from templates and streaming data into the system. If you are using a local installation, you can just use the same virtual environment. However, if you are using Docker, you should create a new local virtual environment to run these commands.

TODO so the 3.10 might not be a hard limit the workshop since we do not install the writing observer (which is where the dependency hell lives).
Tested Python versions: `3.10`
Tested Docker versions: `26.1`

If you do not have Python `3.10`, we suggest you follow the Docker installation option.

You are welcome to use your own instance of redis; however, `docker compose` allows us to spin up an instance of Redis and connect to it. See the Docker Compose section for more information.

The provided run commands all include watchdog turned on to ease development time on re-running the application.

### System Setup

Before starting the system, let's take care of any extra configuration steps.

#### creds.yaml

The `creds.yaml` is the primary configuration file on the system. The platform will not launch unless this file is present. Create a copy of the example in `learning_observer/learning_observer/creds.yaml.example`. We want to make the following adjustments

```bash
cp learning_observer/learning_observer/creds.yaml.example learning_observer/creds.yaml
```

```yaml
auth:
    # remove google_oauth from auth
    # google_oauth: ...

    # enable passwordless insecure log-ins
    # useful for quickly seeing the system up and running
    test_case_insecure: true

# update session information
aio:
    session_secret: asupersecretsessionkeychosenbyyou
    session_max_age: 3600

# If you are using Docker compose, you should change the redis host to
redis_connection:
  redis_host: redis
  redis_port: 6379

# Allow all incoming events
event_auth:
    # ...
    testcase_auth: {}
```

#### admins.yaml & teachers.yaml

The platform expects both of these files to exist under `learning_observer/learning_observer/static_data/`. If these are missing on start-up, the platform create them for you and exit. Normally these are populated with the allowed Admins/Teachers for the system.

#### passwd.lo

Each install of the system needs an admin password file associated with it. The `learning_observer/util/lo_passwd.py` file can be used to generate this password file. This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.

```bash
cd learning_observer/
python util/lo_passwd.py --username admin --password supersecureadminpassword --filename passwd.lo
```

Depending on how the `creds.yaml` authorization settings are configured, you may be required to use the password you create.

### Environments

For the Learning Observer workshop, please use the Docker Compose environment.

#### Local environment

Make sure you are on a fresh virtual environment, then run the install command

```bash
mkvirtualenv lo_workshop
make install
```

To run the system, use the run command

```bash
make run
```

#### Docker

We also support spinning up a Docker container. First build the Docker image, then run it

```bash
docker build -t lo_workshop .   # build the root directory
docker run -it -p 8888:8888 lo_workshop      # -it attaches a terminal, -p attaches local port 8888 to dockers 8888 port
```

Note that building a docker image may take a few minutes.

#### Docker Compose

Docker compose can manage both the normal Dockerfile and an instance of Redis. To both build and turn them on, run

```bash
docker compose up --build

# NOTE: older versions of docker use separate commands for
# building the images and turning them on
docker compose build
docker compose up
```

Watchdog will automatically re-run the command used to run application, `make run`. If we wish to develop while the Docker container is open, we need to modify the `run` command to re-install any packages when it restarts. Your local repository is being shared as a mount to the Docker container. Adding an install command makes sure that latest changes are used.

```Makefile
run:
    pip install -e learning_observer/
    cd learning_observer && python learning_observer --watchdog=restart
```

## Build your own module

### Create from template

We provide a cookiecutter template for creating new modules for the Learning Observer. If you are using Docker, just create a local virtual environment to run this command. To create one run,

```bash
pip install cookiecutter
cd modules/
cookiecutter lo_template_module/
```

Cookiecutter will prompt you for naming information and create a new module in the `modules/` directory.

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
