# identity
Repository of 5G ZORRO Identity and Permissions Manager components source code.

* **Machine requirements**: 
  * Ubuntu 18.04.1 LTS
  * Git 
  * Docker
  * Docker-compose
  * Mongo
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

### Install MongoBD

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
Reference: https://github.com/hyperledger/aries-cloudagent-python/blob/main/demo/README.md#running-in-docker

Git Repository: https://github.com/hyperledger/aries-cloudagent-python

Use below command to download code to your local machine:
```python
git clone https://github.com/hyperledger/aries-cloudagent-python
```
Go to the directory
```python
cd aries-cloudagent-python/demo
```
Now it's possible to initialize the agents. To run the Issuer Agent type:
```python
./run_demo faber
```
Issuer Agent is running on port 8021.
In a new terminal, change directory into aries-cloudagent-python directory of your clone of this repository. Start the Holder Agent by issuing the following command:
```python
./run_demo alice
```
Holder Agent is running on port 8031.
Now perform the same for the Verifier Agent:
```python
./run_demo acme
```
Verifier Agent is running on port 8041.

## Run 5GZorro Agents
* **Requirements**: 
  * Von-network running
  * Agents running
  * Mongo active

Before running this project, you must create an .env file, based on the .env.template available in identity/src. Further detailing can be found in said file.

To run the Identity Controllers, go to identity/src folder, then type in the command line:
```
docker-compose up --build
```
To stop the project, simply type:
```
docker-compose down
```
The Administrator and Trading Provider Controllers should now be available. To access Trading Provider, simply type http://localhost:6800/ on your preferred browser.