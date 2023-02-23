"""定义项目各处中用到的状态码."""


class OperationResult(object):
    """记录如训练、删除等操作状态的对象.

    Attributes:
        code (int): 操作结果状态码
        msg (str): 状态描述
    """

    OPERATION_SUCCESS = 0  # 操作成功
    OPERATION_FAILURE = 1  # 操作失败

    def __init__(self, code, msg):
        """初始化."""
        self.code = code
        self.msg = msg


# FAQ相关
UNK = ""


def get_faq_master_robot_code(robot_code: str) -> str:
    """获取正式环境的faq机器人id."""
    return robot_code + "_master"


def get_faq_test_robot_code(robot_code: str) -> str:
    """获取测试环境的faq机器人id."""
    return robot_code + "_test"


# 闲聊相关
CHITCHAT_FAQ_ID = "chitchat_faq_id"


def get_chitchat_faq_id(robot_id):
    """根据机器人id获取对应的闲聊id，避免在es存储中发生冲突."""
    return robot_id + CHITCHAT_FAQ_ID


# understanding相关参数，0为己理解，1为未理解意图，2为未抽到词槽，3为未匹配到faq知识库问题
UNDERSTAND = "0"
UNDERSTAND_NO_INTENT = "1"
UNDERSTAND_NO_SLOT = "2"
UNDERSTAND_NO_FAQ = "3"
UNDERSTAND_NO_OPTION = "4"

# FAQ默认视角
FAQ_DEFAULT_PERSPECTIVE = "default_perspective"
# 定义答案的几种类型
FAQ_TYPE_NONUSWER = -1  # 没有找到对应的答案
FAQ_TYPE_MULTIANSWER = 1  # 匹配的答案有多种，需要澄清
FAQ_TYPE_SINGLEANSWER = 0  # 匹配到了对应的答案，可以直接回答用户

# nlu相关
NLU_MODEL_USING = "1001"  # 模型正在使用
NLU_MODEL_TRAINING = "1002"  # 模型正在训练
NLU_MODEL_AVALIABLE = "1003"  # 模型可用


# model type
MODEL_TYPE_NLU = ("语义理解",)
MODEL_TYPE_DIALOGUE = "对话流程"
MODEL_TYPE_FAQ = "FAQ"

# 小语平台相关
ALGORITHM_CODE = "XiaoYuRobotOne"
