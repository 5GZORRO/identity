![](https://img.shields.io/badge/python-v3.9.6-brightgreen)
![](https://img.shields.io/badge/fastapi-latest-blue)
![](https://img.shields.io/badge/mongo-latest-blue)
![](https://img.shields.io/badge/docker%20compose-v3-2FBAE0)
[![](https://img.shields.io/badge/packages-up--to--date-brightgreen)](https://github.com/orgs/5GZORRO/packages?repo_name=identity)
[![](https://img.shields.io/badge/license-Apache--2.0-blueviolet)](https://github.com/5GZORRO/identity/blob/main/LICENSE)


# Identity & Permissions Manager
The Identity and Permissions Manager (Id&P) module is responsible for facilitating and coordinating marketplace governance in a decentralized fashion. It supplies the mechanisms required to:
*	Generate unique identifiers in the 5GZORRO ecosystem.
*	Recognise communicating endpoints between the Agents.
*	Identify and authorize entities, services, and organizations to access provisioned services and resources in the 5GZORRO marketplace. 


## Pre-Requisites 
* **System requirements**: 
  * 2 vCPUs
  * 4 GB RAM
  * 60 GB Storage
  * Ubuntu 20.04+ LTS Virtual Machine

* **Software requirements**: 
  * Git 
  * Docker
  * Docker-compose
  * Python
  * VON-Network

## Software requirements installation
### Git
```python
sudo apt-get update
sudo apt-get install git
git --version
```

### Docker
```python
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt update
sudo apt install docker-ce
sudo systemctl status docker
```

### Docker-compose
```python
sudo curl -L “https://github.com/docker/compose/releases/download/1.28.5/docker-compose-$(uname -s)-$(uname -m)” -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```
**Docker compose’s version should be shown.**

### Python
Reference: https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-ubuntu-18-04-quickstart

### Build VON-Network
**If all of the previous steps have been assured, it's now possible to initialize a Von-Network.**

Git Repository: https://github.com/bcgov/von-network

Firstly, clone the project to your local:
```python
git clone https://github.com/bcgov/von-network.git
```
Then, to build & start the network, use:
```python
cd von-network/
sudo ./manage build
sudo ./manage start
```
**All VON-Network nodes should now be active.**

## Configuration
Now we can proceed with the Id&P Agents & Controllers configuration.
### Install & Build Agents
Git Repository: https://github.com/hyperledger/aries-cloudagent-python

**Note: Tested with the 0.6.0 version of aries-cloudagent**

Use below command to download code to your local machine:
```python
git clone https://github.com/hyperledger/aries-cloudagent-python
```
Check the following wiki: https://github.com/5GZORRO/identity/wiki/How-to-install-ACA-PY-0.6.0 to perform the required steps to run the Agents

Now it's possible to initialize the agents. To run the Admin Agent use the command available in https://github.com/5GZORRO/identity/wiki/Admin-Agent-Startup-and-Settings. Admin Agent will be running on port 8021.

Afterwards, run the Regulator Agent similar to in https://github.com/5GZORRO/identity/wiki/Regulator-Agent-Startup-and-Settings.  Regulator Agent will be running on port 8011.

To then run the Holder Agent use the command provided in https://github.com/5GZORRO/identity/wiki/Holder-Agent-Startup-and-Settings. Holder Agent will be running on port 8031.

Finally, run the Verifier Agent by using the command provided in https://github.com/5GZORRO/identity/wiki/Verifier-Agent-Startup-and-Settings. Verifier Agent will be running on port 8041.

### Run Id&P Controllers

Before running this project, you must create an .env file (for Operator B), .env_2 (for Operator C), .env_regulator (for Regulator) & an .env_admin file (for Operator A), based on the .env.template, .env_admin.template & .env_regulator.template files available in identity/src, respectively. Further detailing can be found in said files.

To run the Identity Controllers, go to identity/src folder, then type in the command line:
```
docker-compose up --build
```
To stop the project, simply type:
```
docker-compose down
```
The Administrator, Trader & Regulator Controllers should now be available. To access the Trader, simply type http://localhost:6800/ on your preferred browser.

## Maintainers
**Bruno Santos** - Design & Development - bruno-g-santos@alticelabs.com

## License
This module is distributed under [Apache 2.0 License](LICENSE) terms.