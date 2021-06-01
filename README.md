![](https://img.shields.io/badge/python-v3.8.3-brightgreen)
![](https://img.shields.io/badge/fastapi-latest-blue)
![](https://img.shields.io/badge/mongo-latest-blue)
![](https://img.shields.io/badge/docker%20compose-v3-2FBAE0)
[![](https://img.shields.io/badge/packages-up--to--date-brightgreen)](https://github.com/orgs/5GZORRO/packages?repo_name=identity)
[![](https://img.shields.io/badge/license-Apache--2.0-blueviolet)](https://github.com/5GZORRO/identity/blob/main/LICENSE)


# identity
Repository of 5G ZORRO Identity and Permissions Manager components source code.

* **Machine requirements**: 
  * Ubuntu 20.04 LTS
  * Git 
  * Docker
  * Docker-compose
  * Mongo (optional)
  * Python

## Pre-Requesites 
### Install Git
```python
sudo apt-get update
```
```python
sudo apt-get install git
```
```python
git --version
```

### Install and config Docker
Reference: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04
```python
sudo apt update
```
```python
sudo apt install apt-transport-https ca-certificates curl software-properties-common
```
```python
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```
```python
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
```
```python
sudo apt update
```
```python
sudo apt install docker-ce
```
```python
sudo systemctl status docker
```

### Install Docker-compose
```python
sudo curl -L “https://github.com/docker/compose/releases/download/1.28.5/docker-compose-$(uname -s)-$(uname -m)” -o /usr/local/bin/docker-compose
```
```python
sudo chmod +x /usr/local/bin/docker-compose
```
```python
docker-compose --version
```
Docker compose’s version should be shown.

### Install MongoBD (optional)

This section is aimed for the user that wants to run his own local MongoDB instance.

Reference: https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-18-04-source

### Install Python

Reference: https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-ubuntu-18-04-quickstart

## Build VON-Network
If all of the previous steps have been completed, it is now possible to initialize a Von-Network.

Git Repository: https://github.com/bcgov/von-network

Use below command to download code to your local:
```python
git clone https://github.com/bcgov/von-network.git
```
Go to the directory below
```python
cd von-network/
```
Use below command to build nodes of the network:
```python
sudo ./manage build
```
Use below command to start nodes of the network:
```python
sudo ./manage start
```
All VON-Network nodes should now be active.

## Run Agents 

* **Agents requirements**: 
  * Von-network running
  
### Install Agents
Git Repository: https://github.com/hyperledger/aries-cloudagent-python

Note: Tested with the 0.6.0 version of aries-cloudagent

Use below command to download code to your local machine:
```python
git clone https://github.com/hyperledger/aries-cloudagent-python
```
Check the following wiki: https://github.com/5GZORRO/identity/wiki/How-to-install-ACA-PY-0.6.0 to perform the required steps to run the Agents

Now it's possible to initialize the agents. To run the Issuer Agent use the command available in https://github.com/5GZORRO/identity/wiki/IssuerAgent-Startup-and-Settings. Issuer Agent will be running on port 8021.

To then run the Holder Agent use the command provided in https://github.com/5GZORRO/identity/wiki/Holder-Agent-Startup-and-Settings. Holder Agent will be running on port 8031.

Finally, run the Verifier Agent by using the command provided in https://github.com/5GZORRO/identity/wiki/Verifier-Agent-Startup-and-Settings. Verifier Agent will be running on port 8041.

## Run 5GZorro Agents
* **Requirements**: 
  * Von-network running
  * Agents running
  * Mongo active

Before running this project, you must create an .env file & an .env_admin file, based on the .env.template & .env_admin.template files available in identity/src, respectively. Further detailing can be found in said file.

To run the Identity Controllers, go to identity/src folder, then type in the command line:
```
docker-compose up --build
```
To stop the project, simply type:
```
docker-compose down
```
The Administrator and Trading Provider Controllers should now be available. To access Trading Provider, simply type http://localhost:6800/ on your preferred browser.
