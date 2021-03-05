import requests, json, os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

admin_controller_url = os.environ["ADMIN_CONTROLLER_URL"]

########## CREDENTIAL ISSUING ###########
@app.route('/receive', methods=['POST'])
def handler_receiver():
    global value
    value = request.json
    print(value)
    return value

@app.route('/accept', methods=['GET'])
def handler_sender():
    res_to_admin_agent = {
	    "holder_request_id": value["holder_request_id"],
        "type": value["type"],
        "credentialSubject": {
            "id": value["credentialSubject"]["id"],
            "claims": value["credentialSubject"]["claims"]
        },
        "service_endpoint": value["service_endpoint"]
    }
    
    #print(value["holder_request_id"])
    print(res_to_admin_agent)
    resp = requests.post(admin_controller_url+"/issuer/issue_requested_credential/"+value["_id"], json=res_to_admin_agent, timeout=60) #+"?token=9af0301f-a431-49ac-a7bb-f29fbf2adea3"
    body = resp.json()
    return body

########## STAKEHOLDER REGISTRATION ###########
@app.route('/stakeholder/receive', methods=['POST'])
def handler_stakeholder_receiver():
    global stake_value
    stake_value = request.json
    print(stake_value)
    return stake_value

@app.route('/stakeholder/accept', methods=['GET'])
def handler_stakeholder_sender():
    res_stake_admin_agent = {
	    "holder_request_id": stake_value["holder_request_id"],
        "stakeholderClaim": {
            "governanceBoardDID": stake_value["stakeholderClaim"]["governanceBoardDID"],
            "stakeholderServices": stake_value["stakeholderClaim"]["stakeholderServices"],
            "stakeholderRoles": {
                "role": stake_value["stakeholderClaim"]["stakeholderRoles"]["role"],
                "assets": stake_value["stakeholderClaim"]["stakeholderRoles"]["assets"]
            },
            "stakeholderProfile": {
                "name": stake_value["stakeholderClaim"]["stakeholderProfile"]["name"],
                "address": stake_value["stakeholderClaim"]["stakeholderProfile"]["address"]
            },
            "did": stake_value["stakeholderClaim"]["did"],
            "verkey": stake_value["stakeholderClaim"]["verkey"]
        },
        "service_endpoint": stake_value["service_endpoint"]
    }
    
    #print(stake_value["holder_request_id"])
    print(res_stake_admin_agent)
    resp = requests.post(admin_controller_url+"/issuer/issue_stakeholder/"+stake_value["_id"], json=res_stake_admin_agent, timeout=60)
    body = resp.json()
    return body
#--------------------------------------------------------------------------------------#
if __name__ == "__main__":
    app.run(port='4800', host='0.0.0.0', debug='true')
    