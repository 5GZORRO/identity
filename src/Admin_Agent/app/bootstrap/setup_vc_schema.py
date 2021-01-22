import requests, json, time, sys, os

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

time.sleep(5)

print("#############################################################")
print("############ VERIFIABLE CREDENTIAL SCHEMA SETUP #############")
print("#############################################################")

try:
    # POST VC Schema
    schema = {
      "attributes": [
        "id",
        "type",
        "credentialSubject",
        "issuer",
        "issuanceDate",
        "expirationDate",
        "credentialStatus",
        "proof"
      ],
      "schema_version": "1.0",
      "schema_name": "verifiable_credential"
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
      "tag": "verifiable_cred",
      "schema_id": schema_id_value
    }
    
    cred_def_resp = requests.post(URL+"/credential-definitions", data=json.dumps(cred_definition), headers=header, timeout=60)
    #print(cred_def_resp.text)
    cred_def = json.loads(cred_def_resp.text)
    cred_def_id = cred_def["credential_definition_id"]
    print("VERIFIABLE CREDENTIAL ID: " + str(cred_def_id))

except:
    print(general_message("error", "Unable to create Verifiable Credential schema.", 400))
    sys.exit()

print("########### VERIFIABLE CREDENTIAL SCHEMA SETUP - END ###########")
print("\n")