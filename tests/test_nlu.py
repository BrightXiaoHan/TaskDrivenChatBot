"""
测试nlu训练模型的模块
"""
import os
from backend.nlu import (train_robot,
                         delete_robot,
                         update_training_data,
                         get_interpreter)

cwd = os.path.abspath(os.path.dirname(__file__))


def main():
    # 测试训练nlu模型模型
    robot_code = "_test"
    version = "v1.0"
    nlu_data = open(os.path.join(cwd, "assets/nlu_training_data.json")).read()

    # 强制删除之前的机器人
    delete_robot(robot_code, version, force=True)

    # 上传训练数据并训练模型
    update_training_data(robot_code, version, nlu_data)
    train_robot(robot_code, version)

    # 加载并使用模型
    interpreter = get_interpreter(robot_code, version)
    parse_result = interpreter.parse("我再广州荣悦台小区")
    print(parse_result)

    # 正在使用的模型无法删除
    result = delete_robot(robot_code)
    assert result.code == result.OPERATION_FAILURE

    # 强制删除成功
    result = delete_robot(robot_code, force=True)
    assert result.code == result.OPERATION_SUCCESS


if __name__ == '__main__':
    main()
