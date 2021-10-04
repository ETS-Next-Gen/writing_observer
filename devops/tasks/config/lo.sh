# This is a script to start up Learning Observer with it's own process
# name. This is convenient for being able to start / stop the process.

. /usr/share/virtualenvwrapper/virtualenvwrapper.sh
workon learning_observer
bash -c "exec -a learning_observer python learning_observer" >> lo.log 2>> lo.err
