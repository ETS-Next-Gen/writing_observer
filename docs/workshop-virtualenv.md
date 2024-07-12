Setting up virtualenvwrapper
============================

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) makes it quick and easy to manage Python virtual environments.

1) Install `virtualenvwrapper`. This can be `apt-get install python3-virtualenvwrapper` on Ubuntu, or `pip install virtualenvwrapper` on most other systems.

2) Run it using `source` or `.` (so environment changes stay for the current shell). For one installed with `apt-get`, it will most likely be in `/usr/share/virtualenvwrapper/`. For `pip`, it is often in `~/.local/bin` (and you might need to run `export PATH=~/.local/bin:$PATH`). From `brew` on Mac, it is likely somwhere under `/opt/homebrew/` , `/usr/bin`, `/Users/{home_directory}/Library/Python/` , or `/usr/local/share/` . Please Note that for Mac users,  you might have trouble setting the correct path. You might need to use the command  ` which python3 `, ` which virtualenv ` and ` which virtualenvwrapper.sh ` to get the localization of each item. Here is a [link](https://stackoverflow.com/questions/49470367/install-virtualenv-and-virtualenvwrapper-on-macos), which can help you to troubleshoot the process.

We normally add these three lines to our `.bashrc` so it runs on startup, but you can run these manually:

```bash
# Optionally, pick the place you want your virtual environments
export WORKON_HOME=$HOME/.virtualenvs
# Optionally, pick the Python you want to use.
which python3
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
# Activate virtualenv wrapper
. /usr/share/virtualenvwrapper/virtualenvwrapper.sh # Wherever you installed the script. Note the dot at the beginning! It's important.
```

You now have three commands:

* `mkvirtualenv lo_workshop` makes a virtual environment named `lo_workshop`.
* `workon lo_workshop` switches you to this environment
* `rmvirtualenv lo_workshop` destroys it

There are other commands too, but those are the essentials.
