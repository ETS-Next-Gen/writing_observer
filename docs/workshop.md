# Workshop setup

This document will detail setting Learning Observer platform.

## Requirements

General list of requirests:

- UNIXish system
- Python >3.9 - Tested versions [`3.10`]
- Python dev (????????????????)
- redis
- virtualenv or some other virtual environment manageer
- nano or some other text editor
- Docker (optional) see [Docker section](/#Docker)

We suggest having at least 2 terminals ready for this workshop. The first terminal will be for installing and running the system, while the second will be any additional scripts to need to run.

They should each be on the same virtual environment. You'll need to create a new one `mkvirtualenv` and then switch both terminals to it `workon`.

```bash
mkvirtualenv lo_workshop    # create a new virtual environment OR
workon lo_workshop          # if you already have a virtual environment, switch to it
```

## Install

First make sure you clone the repository

```bash
git clone https://github.com/ETS-Next-Gen/writing_observer.git lo_workshop
cd lo_workshop/
git checkout berickson/workshop # TODO remove this when this branch gets merged in
```

(or with host keys, `git clone git@github.com:ETS-Next-Gen/writing_observer.git lo_workshop`)

NOTE: all future sets of commands should be ran starting from the repository's root directory. The command will specify if changing directories is needed.

### Environments

Make sure you are on the virtual environment, then run the install command:

```bash
make install
```

### System Setup

Before starting the system, let's take care of any extra configuration steps.

#### creds.yaml

The `creds.yaml` is the primary configuration file on the system. The platform will not launch unless this file is present. Create a copy of the example in `learning_observer/learning_observer/creds.yaml.example`. We want to make the following adjustments

```bash
cp learning_observer/learning_observer/creds.yaml.example learning_observer/creds.yaml
nano learning_observer/creds.yaml   # or a different text editor
```

```yaml
auth:
    # remove google_oauth from auth
    # google_oauth: ...

    # enable passwordless insecure log-ins
    # useful for quickly seeing the system up and running
    test_case_insecure: true

# Make sure the redis_connection is pointed at the right host
redis_connection:
  redis_host: localhost
  redis_port: 6379

# Typically students need to be associated with a classroom; however,
# specifying `all` creates a single class with all available students.
roster_data:
    source: all

# update session information
aio:
    session_secret: asupersecretsessionkeychosenbyyou
    session_max_age: 3600

# Allow all incoming events
event_auth:
    # ...
    testcase_auth: {}
```

#### admins.yaml & teachers.yaml

The platform expects both of these files to exist under `learning_observer/learning_observer/static_data/`. If these are missing on start-up, the platform create them for you and exit. Normally these are populated with the allowed Admins/Teachers for the system.

## Running Learning Observer

Once all the dependencies are installed and configuration is taken care of, you can continue with running the Learning Observer platform

```bash
make run
```

## Build your own module

### Create from template

We provide a cookiecutter template for creating new modules for the Learning Observer. If you are using Docker, just create a local virtual environment to run this command. To create one run,

```bash
cd modules/
cookiecutter lo_template_module/
```

Cookiecutter will prompt you for naming information and create a new module in the `modules/` directory.

### Installing

To install the newly created project, use `pip` like any other Python package.

```bash
pip install -e modules/learning_observer_template/  # -e installs in develop mode so changes are reflected in the package immediately
```

## Streaming Data

We can stream data into the system to simulate a classroom of students working. Once Learning Observer is up and running, run

```bash
python learning_observer/util/stream_writing --fake-name --url=localhost:8888 --streams=10
```

This will generate events for 10 students typing a set of loremipsum texts and send them to `localhost:8888`. As students appear on Learning Observer, they will automatically be included in the overall classroom.

## Docker

This section details what is needed for using installing the system with Docker.

This has been tested with Docker versions [`26.1`].

### Dockerfile

We also support spinning up a Docker container. First build the Docker image, then run it

```bash
docker build -t lo_workshop .   # build the root directory and tag it (-t) as `lo_workshop`
docker run -it -p 8888:8888 lo_workshop      # -it attaches a terminal, -p attaches local port 8888 to dockers 8888 port
```

Note that building a docker image may take a few minutes.

### Docker compose

Docker compose can manage both the normal Dockerfile and an instance of Redis. Docker compose will serve Redis at hostname `redis`. Make sure to modify `creds.yaml` with the updated hostname before continuing.

To both build and turn them on, run

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

### Installing additional modules

If you wish to install additional modules and continue doing development, you should add the module install to the `make run` command.

```Makefile
run:
    pip install -e learning_observer/
    pip install -e modules/learning_observer_template/
    cd learning_observer && python learning_observer --watchdog=restart
```

## Common errors

Here are a list of common errors encountered while setting up the system.

- Your system firewall settings may block you from communicating with specific ports
- Older versions of Docker may use different syntax
- If your Redis instance requires a password, include it in `creds.yaml` and uncomment the password parameter line in the `learning_obersver/redis_connection.py` file. There is a bug regarding defaults in the settings package, `pmss`.
