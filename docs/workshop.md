# Learning Observer Workshop

This document will step you through the Learning Observer workshop. Our goals for this workshop are: 

* Give an overview of the platform
* Collect feedback on how to make the platform useful for your own work
* Collect feedback on different major components of the platform
* Have fun hacking learning analytics together

We recommend working in groups of three. This way:

* You can help each other
* At least one person will (hopefully) have a working machine

We suggest having at least **2 terminals** ready for this workshop. The first terminal will be for installing and running the system, while the second will be any additional scripts to need to run.

Prerequisites:

* Unix-style system
  * Ubuntu is most tested
  * MacOS should work as well, but is less tested
  * Windows should work with WSL, but you'll need to [install it beforehand](wsl-install.md).
* `python 3`. We tested and recommend 3.10 and 3.11, but anything newer than 3.9 should work

Recommendations:

* `virtualenvwrapper`. If you prefer a different package management system, you can use that instead.

Options:

* `redis`. We need a key-value store. However, if you don't have this, we can use files on the file system or in-memory. If you use `docker compose`, it will spin this up for you. Beyond this workshop, we strongly recommend using a `redis` (the recommended `redis` going forward is [ValKey](https://en.wikipedia.org/wiki/Valkey), as opposed to redis proprietary)
* `docker`. We're not big fans of `docker` for this type of work, so this pathway is less tested. However, by popularity, we do provide a `docker` option. We tested with docker 26.1. You should only use this if you're fluent in `docker`, since you'll probably need to tweak instructions slightly (especially if you're not on 26.1).

If you'd like to use `docker`, we have a quick [tutorial](docker.md).

If you can install the prerequisites before the workshop, it will save a lot of time, and not put us at risk of issues due to hotel bandwidth.

We have a document with a more in-depth overview of the [technologies](technologies.md) we use.

### Python environment

We recommend working in a Python environment of some sort. Our preferred tool is [virtualenvwrapper](https://pypi.org/project/virtualenvwrapper/). You are welcome to use your own (`anaconda`, or as you prefer). `virtualenvwrapper` lets you manage packages and dependencies without making a mess on your computer. 

If you don't have a way of managing Python virtual environments, or would prefer to use `virtualenvwrapper`, we have a [short guide](workshop-virtualenv.md). *We strongly recommend working in some virtual environment, however*. 

## Download

First make sure you clone the repository:

```bash
git clone https://github.com/ETS-Next-Gen/writing_observer.git lo_workshop
```

**or**, if you have a github account properly configured with ssh:

```bash
git clone git@github.com:ETS-Next-Gen/writing_observer.git lo_workshop
```

```bash
cd lo_workshop/
git checkout berickson/workshop # This is a branch we set up with some extra things for this workshop!
```

NOTE: All future commands should be ran starting from the repository's root directory. The command will specify if changing directories is needed.

## Local environment

Make sure you are on a fresh virtual environment. In `virtualenvwrapper`:

```bash
mkvirtualenv lo_workshop
workon lo_workshop```

Then run the install command:

```bash
make install
```

This will download required backpages. This might take a while, depending on hotel bandwidth.

## Configuration

Before starting the system, let's take care of any extra configuration steps. We are currently in the process of moving configuration formats from YAML to [PMSS](https://github.com/ETS-Next-Gen/pmss).

We may discuss this in the workshop later, but for now, we will configure using YAML.

We need a system configuration for this workshop. You can copy over this file with the command below, or you can make the changes yourself as per [these instruction](/docs/workshop_creds.md). In essence, the changes are:

1. Disable teacher authentication. We have pluggable authentication schemes, and we disable Google oauth and other schemes.
2. Disable learning event authentication. Ditto, but for incoming data.
3. Give a key for session management. This should be unique for security
4. Switch from redis to on-disk storage. We have pluggable databases. On-disk storage means you don't need to install redis.

Making these yourself is a good exercise. Note we are switching configuration formats, but the options will stay the same.

Copy the workshop `creds.yaml` file:

```bash
cp learning_observer/learning_observer/creds.yaml.workshop learning_observer/creds.yaml
```

If you have a file comparison tool like `meld`, it might be worth comparing our changes: `meld learning_observer/creds.yaml learning_observer/learning_observer/creds.yaml.example`

## Test the system

To run the system, use the run command

```bash
make run
```

*This does a lot of sanity checks on startup, and won't work the first time.* Rather, it will download required files, and create a file files (like `admins.yaml` and `teachers.yaml`, which are one way to define roles for teachers and admins on the system, but which we won't need for this workshop since we are using an insecure login). Once it is done, it will give you an opportunity to check whether it fixed issues correctly. It did, so just run it again:

```bash
make run
```

You should be able to navigate to either `http://localhost:8888/`, `http://0.0.0.0:8888/`, or `http://127.0.0.1:8888/`, depending on your operating system, and see a list of courses and analytics modules. None are installed. We'll build one next!

## Build your own module

### Create from template

We provide a cookiecutter template for creating new modules for the Learning Observer. If you are using Docker, just create a local virtual environment to run this command. To create one run,

```bash
cd modules/
cookiecutter lo_template_module/
```

Cookiecutter will prompt you for naming information and create a new module in the `modules/` directory. By default, this is called `learning_observer_template`, but pick your own name and substitute it into the commands below. 

### Installing

To install the newly created project, use `pip` like any other Python package.

```bash
pip install -e learning_observer_template/
```

## Streaming Data

We can stream data into the system to simulate a classroom of students working. Once the system is up and running, open **a new terminal** and run

```bash
workon lo_workshop
python learning_observer/util/stream_writing.py --streams=10
```

This will generate events for 10 students typing a set of loremipsum texts and send them to the story.

This does not have to be done in the same virtual environment as the main server. If you are using Docker, just create a local virtual environment to run this command.
