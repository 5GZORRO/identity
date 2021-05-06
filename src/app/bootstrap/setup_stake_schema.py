import requests, json, time, sys, os

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

def stakeholder_cred_setup():
    print("\n")
    print("#############################################################")
    print("############ STAKEHOLDER CREDENTIAL SCHEMA SETUP ############")
    print("#############################################################")

    try:
        # POST AUTH Schema
        schema = {
            "attributes": [
                "stakeholderClaim",
                "timestamp"
            ],
            "schema_version": "1.0",
            "schema_name": "stakeholder_cred"
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
        "tag": "stakeholder_cred",
        "schema_id": schema_id_value
        }
        
        cred_def_resp = requests.post(URL+"/credential-definitions", data=json.dumps(cred_definition), headers=header, timeout=60)
        #print(cred_def_resp.text)
        cred_definition = json.loads(cred_def_resp.text)
        global cred_def_id
        cred_def_id = cred_definition["credential_definition_id"]
        '''
        # POST AUTH Credential 
        issue_cred = {
            #"connection_id": "634e9c74-4c46-4d5c-9df1-3e2b65a53792",
            "cred_def_id": cred_definition["credential_definition_id"],
            "credential_proposal": {
                "attributes": [
                    {
                        "name": "name",
                        "value": "admin_auth_cred"
                    },
                    {
                        "name": "description",
                        "value": "admin_auth_cred"
                    }
                ]
            }
        }
        #print(issue_cred)

        final_resp = requests.post(URL+"/issue-credential/create", data=json.dumps(issue_cred), headers=header, timeout=60)
        #print(final_resp.text)
        cred_info = json.loads(final_resp.text)
        id_token = cred_info["credential_exchange_id"]
        print("ID TOKEN: "+ str(id_token))
        '''

    except:
        print(general_message("error", "Unable to emit Admin Auth Credential.", 400))
        sys.exit()

    #id_token = "develop_teste"
    #print("ID TOKEN: "+ str(id_token))
    print("STAKEHOLDER CRED DEF ID: " + str(cred_def_id))
    print("############## STAKEHOLDER CREDENTIAL SCHEMA SETUP - END ##############")
    print("\n")