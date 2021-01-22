#from fastapi import FastAPI
import requests, json, time, sys, os
'''
def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

print("#############################################################")
print("#################### VERIFIER CONNECTION ####################")
print("#############################################################")
#connection_id = "teste_2"

try:
    URL = os.environ["VERIFIER_AGENT_URL"]
    resp = requests.post(URL+"/connections/create-invitation", headers=header, timeout=30)
    body = resp.json()
    connection_id = body["connection_id"]
    conn_invite = json.dumps(body["invitation"], indent = 4)
    print(connection_id)
    print(conn_invite)
except:
    print(general_message("error", "Unable to post Invitation.", 400))
    sys.exit()

try:
    URL_holder = os.environ["HOLDER_AGENT_URL"]
    resp_accept = requests.post(URL_holder+"/connections/receive-invitation", data=conn_invite, headers=header, timeout=30)
    body_accept = resp_accept.json()
    print(body_accept)
except:
    print(general_message("error", "Unable to accept Invitation.", 400))
    sys.exit()

time.sleep(10)

try:
    resp_confirm_active = requests.get(URL+"/connections/"+connection_id, timeout=30)
    body_active = resp_confirm_active.json()
    if body_active["state"] == 'active':
        #log_message(200, "Issuer Connection established successfully.")
        print(general_message("success", "Verifier Connection established successfully.", 200))
except:
    print(general_message("error", "Unable to establish Verifier Connection.", 400))
    sys.exit()
'''
print("#################### VERIFIER CONNECTION - END ####################")
print("\n")