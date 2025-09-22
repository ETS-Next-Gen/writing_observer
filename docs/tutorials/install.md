# Formative Process for Writing - Installation Instructions
Last updated: 16-JAN-2020

## Install Chrome Extension
* Set up a github SSH key.
* Download the extension code:
```bash
cd
git clone https://github.com/ETS-Next-Gen/writing_analysis.git writing_analysis
```
* Navigate to `chrome://extensions`.
* Click on "Load Unpacked". Select ~/writing_anlysis/extensions

## Create an AWS account and an EC2 instance.
* Select Ubuntu, nano AMI. The cost should be 0.5 cents per hour.
* In security groups, add HTTP, HTTPS rules. Open up only to your computer's IP address (the client).
* Launch instance.
* Suppose your instance public DNS is {ec2_ip}, e.g., ec2-18-223-122-172.us-east-2.compute.amazonaws.com.
* Create aSSH key pair, save PEM file say under ~/.ssh, chmod to u+r.

## Set up the EC2 instance.
* SSH into the machine: `bash ssh -i {pem_file} ubuntu@{ec2_ip}`.
* (Optional) Create a user account: sudo useradd {user}
* Download the server code (same repository as the extension):
```bash
cd
git clone https://github.com/ETS-Next-Gen/writing_analysis.git writing_analysis
```
* Install Ansible.
```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install ansible
````
* Configure Ansible.
sudo pico /etc/ansible/hosts
Add
```
[localhost]
127.0.0.1
```
* `cd ~/writing_analysis/configuration`.
* Run `sudo ansible-playbook local.yaml`. This may take a while on an EC2 nanon machine.
If all goes well, you should see an output with no errors, like this:
```
bash
...
PLAY RECAP ******************************************************************************************
127.0.0.1                  : ok=5    changed=4    unreachable=0    failed=0   
```
* Navigate to http://{ec2_ip}; you should see the message "Welcome to nginx!" if it's working.

## Obtain a free domain name
* Go to noip.com.
* Sign up 

## Obtain a free SSL Certificate Using Certbot
* Run the following commands:
```bash
sudo apt-get install software-properties-common
Sudo add-apt-repository universe
sudo add-apt-repository ppa:certbot/certbot
sudo apt-get update
sudo apt-get install certbot python-certbot-nginx
```
```
bash
sudo certbot --nginx
```
-- Put in your {mydomain}.hopto.org address.
-- Choose 1 - no redirect.

## Stand up a backend server on the EC2 instance.
