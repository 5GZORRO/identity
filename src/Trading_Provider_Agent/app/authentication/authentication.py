import requests, json, time, sys, os

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

print("#############################################################")
print("########## TRADING PROVIDER AGENT AUTH CREDENTIAL ###########")
print("#############################################################")

try:
    # POST AUTH Schema
    schema = {
      "attributes": [
        "name",
        "description"
      ],
      "schema_version": "1.0",
      "schema_name": "trade_provider_auth"
    }
    
    URL = os.environ["ISSUER_AGENT_URL"]
    resp = requests.post(URL+"/schemas", data=json.dumps(schema), headers=header, timeout=30)
    #print(resp.text)
    
    schema = json.loads(resp.text)
    schema_id_value = schema["schema_id"]
    #print(schema_id_value)
    
    # POST Credential Definition
    cred_definition = {
      "support_revocation": False,
      "tag": "trade_provider_auth",
      "schema_id": schema_id_value
    }
    
    cred_def_resp = requests.post(URL+"/credential-definitions", data=json.dumps(cred_definition), headers=header, timeout=60)
    #print(cred_def_resp.text)
    cred_definition = json.loads(cred_def_resp.text)

    # POST AUTH Credential 
    issue_cred = {
        #"connection_id": "634e9c74-4c46-4d5c-9df1-3e2b65a53792",
        "cred_def_id": cred_definition["credential_definition_id"],
        "credential_proposal": {
            "attributes": [
                {
                    "name": "name",
                    "value": "trade_provider_cred"
                },
                {
                    "name": "description",
                    "value": "trade_provider_cred"
                }
            ]
        }
    }
    #print(issue_cred)

    final_resp = requests.post(URL+"/issue-credential/create", data=json.dumps(issue_cred), headers=header, timeout=60)
    #print(final_resp.text)
    cred_info = json.loads(final_resp.text)
    id_token = cred_info["credential_exchange_id"]
    print("TRADING PROVIDER ID TOKEN: "+ str(id_token))

except:
    print(general_message("error", "Unable to emit Trading Provider Auth Credential.", 400))
    sys.exit()

print("######## TRADING PROVIDER AGENT AUTH CREDENTIAL - END ########")
print("\n")