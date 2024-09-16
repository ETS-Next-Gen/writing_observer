#!/usr/bin/bash

# This is a script to start up toy-sba with it's own process
# name. This is convenient for being able to start / stop the process.

cd /home/ubuntu/toy-sba
bash -c "sudo -E npm run dev" >> /home/ubuntu/toy_sba.log 2>> /home/ubuntu/toy_sba.err
