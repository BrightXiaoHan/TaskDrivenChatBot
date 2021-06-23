"""测试faq引擎相关api
"""
import os
import time
import json
from config import global_config
from utils.define import UNK
global_config["_delay_loading_robot"] = True

import backend.faq as faq


def main():
    robot_code = "test_robot_id"
    cwd = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cwd, 'assets/faq_training_data.json')) as f:
        data = json.load(f)
    faq.faq_update(robot_code, data)

    # wait for engine ready
    time.sleep(10)

    answer = faq.faq_ask(robot_code, data[0]["title"])
    assert answer["answer"] == data[0]["answer"]
    answer = faq.faq_ask(robot_code, data[1]["title"])
    assert answer["answer"] == data[1]["answer"]

    faq.faq_delete(robot_code, {"faq_ids": data[0]["faq_id"]})

    # wait for engine ready
    time.sleep(10)

    answer = faq.faq_ask(robot_code, data[0]["title"])
    assert answer["faq_id"] == UNK

    faq.faq_delete_all(robot_code)
    # wait for engine ready
    time.sleep(10)

    answer = faq.faq_ask(robot_code, data[1]["title"])
    assert answer["faq_id"] == UNK


if __name__ == "__main__":
    main()
