import requests, json, time, sys, os
from loguru import logger

header = {
    'Content-Type': 'application/json'        
}

def stake_license_cred_setup():
    # POST AUTH Schema
    try:
        schema = {
            "attributes": [
                "stakeholderServices",
                "licenseDID",
                "timestamp"
            ],
            "schema_version": "1.0",
            "schema_name": "stake_license_cred"
        }
        
        URL = os.environ["ISSUER_AGENT_URL"]

        logger.info('--- Sending /schemas (license):')
        logger.info(schema)

        resp = requests.post(URL+"/schemas", data=json.dumps(schema), headers=header, timeout=30)
        #print(resp.text)
        
        schema = json.loads(resp.text)
        schema_id_value = schema["schema_id"]
    
    except Exception as error:
        logger.error(error)

    # POST Credential Definition
    try:
        cred_definition = {
        "support_revocation": False,
        "tag": "stake_license_cred",
        "schema_id": schema_id_value
        }

        logger.info('--- Sending /credential-definitions:')
        logger.info(cred_definition)

        cred_def_resp = requests.post(URL+"/credential-definitions", data=json.dumps(cred_definition), headers=header, timeout=60)
        #print(cred_def_resp.text)
        cred_definition = json.loads(cred_def_resp.text)
        global cred_def_id
        cred_def_id = cred_definition["credential_definition_id"]
        logger.info("Stakeholder License Credential Definition id: " + str(cred_def_id))

    except Exception as error:
        logger.error(error)
