"""
测试nlu训练模型的模块
"""
import os
from backend.nlu import (train_robot,
                         delete_robot,
                         create_lock,
                         release_lock,
                         update_training_data)
from utils.define import NLU_MODEL_USING

cwd = os.path.abspath(os.path.dirname(__file__))


def main():
    # 测试训练nlu模型模型
    robot_code = "_test"
    version = "v1.0"
    nlu_data = open(os.path.join(cwd, "assets/nlu_training_data.json")).read()
    dialogue_graph = open(os.path.join(
        cwd, "assets/dialogue_graph.json")).read()

    delete_robot(robot_code, version)
    update_training_data(robot_code, version, nlu_data, dialogue_graph)
    train_robot(robot_code, version)

    # lock model
    create_lock(robot_code, version, NLU_MODEL_USING)
    result = delete_robot(robot_code, version)
    assert result.code == result.OPERATION_FAILURE
    release_lock(robot_code, version)
    result = delete_robot(robot_code)
    assert result.code == result.OPERATION_SUCCESS


if __name__ == '__main__':
    main()
