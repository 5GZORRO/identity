import requests, json, time, sys, os
from timeloop import Timeloop
from datetime import timedelta

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

#tl = Timeloop()

#@tl.job(interval=timedelta(seconds=86400))
def issuer_key_create():
    try:
        print("\n")
        print("####################################################")
        print("#################### ISSUER KEY ####################")
        print("####################################################")
        holder_url = os.environ["ISSUER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        #did = result["result"]["did"]
        global verkey
        verkey = result["result"]["verkey"]
        print("Verification Key: " + str(verkey))
        print("#################### ISSUER KEY - END ####################")
        print("\n")
    except:
        print(general_message("error", "Unable to create bootstrap verification key.", 400))
        sys.exit()

#tl.start(block=False)