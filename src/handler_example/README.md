# Demo Handler for Stakeholder and DID acceptance
* **Requirements**: 
  * 5GZorro Agents Running
  * Docker
  * dot-env

To run this handler example, simply type in the command line:
```
docker-compose up --build
```
To stop the project, simply type:
```
docker-compose down
```
The handler should be running on port 4800.

## Pre-Requisites
### Install and config Docker
(Tutorial of configuration available in main ReadMe)

## Demo Handler Operations
### Accept Stakeholder
After using the register_stakeholder endpoint on the 5GZorro Provider, an event should be sent from the 5GZorro Admin to this handler's /stakeholder/receive endpoint.
You can check the received information on the handler's console. To accept this stakeholder registry, type http://localhost:4800/stakeholder/accept

### Accept DID Credential
When using the create_did endpoint on the 5GZorro Provider, likewise to the Stakeholder process, an event should be sent from the 5GZorro Admin to this handler /receive endpoint.
The DID can be seen as well on the handler's console. To accept it, type http://localhost:4800/accept on your prefered browser. This should register the Credential on the Agent's wallet.