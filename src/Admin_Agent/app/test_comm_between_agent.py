import requests, json, time, sys, os

def general_message(status, message, code):
    response = {"status": status, "message": message, "code": code}
    return json.dumps(response, indent = 4)

header = {
    'Content-Type': 'application/json'        
}

time.sleep(5)

print("###################################################################")
print("###################### GET EVENT TO REGULATOR #####################")
print("###################################################################")
try:
    URL = os.environ["REGULATOR_AGENT_CONTROLLER_URL"]
    resp = requests.get(URL+"/dids/read", timeout=20)
    body = resp.json()
    print("\n")
    print(body)
    print("\n")
except:
    print(general_message("error", "Unable to request to Regulator Agent Controller.", 400))
    sys.exit()
print("################## GET EVENT TO REGULATOR - END ##################")
print("\n")

time.sleep(5)

print("###################################################################")
print("###################### POST EVENT TO REGULATOR ####################")
print("###################################################################")
try:
    URL = os.environ["REGULATOR_AGENT_CONTROLLER_URL"]
    resp = requests.post(URL+"/dids/create?did=teste&verkey=teste", timeout=20)
    body = resp.json()
    print("\n")
    print(body)
    print("\n")
except:
    print(general_message("error", "Unable to request to Regulator Agent Controller.", 400))
    sys.exit()
print("################## POST EVENT TO REGULATOR - END ##################")
print("\n")

print("########################################################################")
print("###################### POST JSON EVENT TO REGULATOR ####################")
print("########################################################################")
try:
    URL = os.environ["REGULATOR_AGENT_CONTROLLER_URL"]
    body_auth = {
        "username":"teste@user.com", 
        "password":"N9kF8NyS5GC8zRh",
        "company": {
            "name":"Placeholder",
            "type":"unsecure"
        }
    }
    resp = requests.post(URL+"/dids/register", headers=header, json=body_auth, timeout=20)
    body = resp.json()
    print("\n")
    print("Returned body: " + str(body))
    print("\n")
except:
    print(general_message("error", "Unable to request to Regulator Agent Controller.", 400))
    sys.exit()
print("################## POST JSON EVENT TO REGULATOR - END ##################")
print("\n")