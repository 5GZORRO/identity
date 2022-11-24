import requests, json, time, sys, os
from loguru import logger

header = {
    'Content-Type': 'application/json'        
}

#time.sleep(5)
def vc_setup():
  # POST VC Schema
  try:
      schema = {
        "attributes": [
          "type",
          "credentialSubject",
          "timestamp"
        ],
        "schema_version": "1.0",
        "schema_name": "verifiable_cred_with_revoke"
      }
      
      URL = os.environ["ISSUER_AGENT_URL"]
      logger.info('--- Sending /schemas (vc):')
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
        #"revocation_registry_size": 32000,
        #"support_revocation": True,
        "support_revocation": False,
        "tag": "verifiable_cred_with_revoke",
        "schema_id": schema_id_value
      }
      
      logger.info('--- Sending /credential-definitions (vc):')
      logger.info(cred_definition)
  
      cred_def_resp = requests.post(URL+"/credential-definitions", data=json.dumps(cred_definition), headers=header, timeout=60)
      #print(cred_def_resp.text)
      cred_def = json.loads(cred_def_resp.text)
      global cred_def_id
      cred_def_id = cred_def["credential_definition_id"]
      logger.info("DID Credential Definition id: " + str(cred_def_id))

  except Exception as error:
      logger.error(error)
