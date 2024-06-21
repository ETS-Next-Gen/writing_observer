# Workshop setup

This document will detail setting Learning Observer platform.

## Install

First make sure you have clone the system

```bash
git clone git@github.com:ETS-Next-Gen/writing_observer.git
git checkout berickson/workshop # TODO remove this when this all gets merged
```

### Technologies

The Learning Observer is ran as a Python aiohttp web application. The primary database used alongside is Redis.

TODO so the 3.10 might not be a hard limit the workshop since we do not install the writing observer (which is where the dependency hell lives).
Tested Python versions: `3.10`
Tested Docker versions: `26.1`

If you do not have Python `3.10`, we suggest you follow the Docker installation option.

You are welcome to use your own instance of redis; however, `docker compose` allows us to spin up an instance of Redis and connect to it. See the Docker & Redis section for more information.

The provided run commands all include watchdog turned on to ease development time on re-running the application.

### Local environment

Make sure you are on a fresh virtual environment, then run the install command

```bash
mkvirtualenv lo_workshop
make install
```

To run the system, use the run command

```bash
make run
```

### Docker

We also support spinning up a Docker container. First build the Docker image, then run it

```bash
docker build -t lo_workshop .   # build the root directory
docker run -it -p 8888:8888 lo_workshop      # -it attaches a terminal, -p attaches local port 8888 to dockers 8888 port
```

Note that building a docker image may take a few minutes.

### Docker & Redis

Docker compose can manage both the normal Dockerfile and an instance of Redis. To both build and turn them on, run

```bash
docker compose up
```

## Running the System

When the system first starts up, it checks for various configuration files.

### creds.yaml

The `creds.yaml` is the primary configuration file on the system. The platform will not launch unless this file is present. Create a copy of the example in `learning_observer/learning_observer/creds.yaml.example`. We want to make the following adjustments

```yaml
```

### admins.yaml & teachers.yaml

The platform expects both of these files to exist under `learning_observer/learning_observer/static_data/`. If these are missing on start-up, the platform create them for you and exit.

### passwd.lo

Each install of the system needs an admin password file associated with it. The `learning_observer/util/lo_passwd.py` file can be used to generate this password file. This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.

```bash
cd learning_observer/
python util/lo_passwd.py
```

Depending on how the `creds.yaml` authorization settings are configured, you may be required to use the password you create.

## Streaming Data

We can stream data into the system to simulate a classroom of students working. Once the system is up and running, run

```bash
python learning_observer/util/stream_writing --fake-name --gpt3=argument --url=localhost:8888
```

This will generate events using fake names for a set of text (`argument`/`story`) and send them to `localhost:8888`.

This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.
