"""
定义项目各处中用到的状态码
"""


class OperationResult(object):
    """记录如训练、删除等操作状态的对象

    Attributes:
        code (int): 操作结果状态码
        msg (str): 状态描述
    """
    OPERATION_SUCCESS = 0  # 操作成功
    OPERATION_FAILURE = 1  # 操作失败

    def __init__(self, code, msg):
        self.code = code
        self. msg = msg


# nlu相关
NLU_MODEL_USING = "1001"  # 模型正在使用
NLU_MODEL_TRAINING = "1002"  # 模型正在训练
NLU_MODEL_AVALIABLE = "1003"  # 模型可用


# model type
MODEL_TYPE_NLU = "语义理解",
MODEL_TYPE_DIALOGUE = "对话流程"
MODEL_TYPE_FAQ = "FAQ"

# 小语平台相关
ALGORITHM_CODE = "XiaoYuRobotOne"
