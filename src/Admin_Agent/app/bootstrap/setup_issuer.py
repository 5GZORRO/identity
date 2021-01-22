#from fastapi import FastAPI
import requests, json, time, sys, os #, logging
#from datetime import date, datetime, timedelta

#dt = datetime.today()
#logging.basicConfig(filename='logs/'+str(dt.year)+'-'+str(dt.month)+'.json', level=logging.INFO, format='{ "timestamp": "%(asctime)s", "component": "adapter", %(message)s}', datefmt='%Y-%m-%d %H:%M:%S')

#start_time = time.time()
#def log_message(status, message):
#    end_time = round(time.time() - start_time, 6)
#    logging.info('"execution_time": '+str(end_time)+', "status": "'+str(status)+'", "message": "'+message+'"')
#    return

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

print("###########################################################")
print("#################### ISSUER CONNECTION ####################")
print("###########################################################")
#connection_id = "teste"

try:
    URL = os.environ["ISSUER_AGENT_URL"]
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
        print(general_message("success", "Issuer Connection established successfully.", 200))
except:
    print(general_message("error", "Unable to establish Issuer Connection.", 400))
    sys.exit()

print("#################### ISSUER CONNECTION - END ####################")
print("\n")