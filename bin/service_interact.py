import os
import json
from config import global_config
from utils.funcs import post_rpc

serve_port = global_config["serve_port"]

cwd = os.path.abspath(os.path.dirname(__file__))
params = json.load(open(os.path.join(cwd, "params.json")))

data = {
    "robotId": params["robot_code"],
    "userCode": "user1",
    "params": params["params"]
}
response = post_rpc(
    "http://127.0.0.1:{}/api/v1/session/create".format(serve_port),
    data
)
print(response)

while True:
    says = input("用户说：")
    data = {
        "robotId": params["robot_code"],
        "userCode": "user1",
        "sessionId": response["data"]["sessionId"],
        "userSays": says
    }
    response = post_rpc(
        "http://127.0.0.1:{}/api/v1/session/reply".format(serve_port),
        data
    )
    print(response)
