import logging
import traceback

EXCEPTION_LOGGER = logging.getLogger("XiaoYuException")


class XiaoYuBaseException(Exception):
    """
    小语机器人基础异常

    Attributes:
        ERR_CODE (int): 错误码, 需要被子类覆盖
    """
    ERR_CODE = 0x000

    def log_err(self):
        """
        记录错误消息到日志
        """
        EXCEPTION_LOGGER.error(traceback.format_exc())
        EXCEPTION_LOGGER.error(self.err_msg())

    def err_msg(self):
        """
        遇到项目抛出此异常返回给web api调用者的信息（可用于前端展示给用户）
        子类必须实现此方法
        """
        raise NotImplementedError


class RpcException(XiaoYuBaseException):
    """
    外部请求调用异常

    Atrributes:
        request_url (str): 所请求的服务地址
        request_data (dict): 请求的参数，字典类型的数据
        response_text (str): 服务返回的内容
    """
    ERR_CODE = 0x001

    def __init__(self, request_url, request_data, response_text, *args):
        super().__init__(*args)
        self.request_url = request_url
        self.request_data = request_data
        self.response_text = response_text

    def err_msg(self):
        msg = "系统调用外部接口错误，请通知管理员检查。\n"
        msg += "request url: {}\n".format(self.request_url)
        msg += "request data: {}\n".format(str(self.request_data))
        msg += "response_text: {}\n".format(self.response_text)
        return msg


class LoadTrainingModelException(XiaoYuBaseException):
    """加载了正在训练中的模型

    Atrributes:
        robot_code (str): 机器人唯一标识
        version (str): 所加载的模型版本
        model_type (str): "语义理解"，"对话流程"，"FAQ"其中之一
    """
    ERR_CODE = 0x002

    def __init__(self, robot_code, version, model_type):
        self.robot_code = robot_code
        self.version = version
        self.model_type = model_type

    def err_msg(self):
        msg = "您可能加载了还未训练完成的模型，请等待等待模型训练完毕后重新加载\n"
        msg += "robot_code: {}\n".format(self.robot_code)
        msg += "version: {}\n".format(self.version)
        msg += "model_type: {}\n".format(self.model_type)
        return msg


class ConversationNotFoundException(XiaoYuBaseException):
    """指定的对话id没有找到的错误

    Attributes:
        robot_code (str): 机器人唯一标识
        conversation_id (str): 会话唯一标识
    """
    ERR_CODE = 0x003

    def __init__(self, robot_code, conversation_id):
        self.robot_code = robot_code
        self.conversation_id = conversation_id

    def err_msg(self):
        msg = "指定对话不存在，您的对话可能已经超时，请重新建立链接"
        msg += "robot_code: {}\n".format(self.robot_code)
        msg += "conversation_id: {}\n".format(self.conversation_id)
        return msg


class NoAvaliableModelException(XiaoYuBaseException):
    """系统启动时没有找到可用的模型，当指定的模型版本不存在时会报此错误

    Atrributes:
        robot_code (str): 机器人唯一标识
        version (str): 所加载的模型版本
        model_type (str): "语义理解"，"对话流程"，"FAQ"其中之一
    """
    ERR_CODE = 0x005

    def __init__(self, robot_code, version, model_type):
        self.robot_code = robot_code
        self.version = version
        self.model_type = model_type

    def err_msg(self):
        msg = "模型版本不存在，请检查模型版本是否可用\n"
        msg += "robot_code: {}\n".format(self.robot_code)
        msg += "version: {}\n".format(self.version)
        msg += "model_type: {}\n".format(self.model_type)
        return msg


class ModelBrokenException(XiaoYuBaseException):
    """当请求加载指定模型而模型已经损坏，则会报此错误

    Atrributes:
        robot_code (str): 机器人唯一标识
        version (str): 所加载的模型版本
        model_type (str): "语义理解"，"对话流程"，"FAQ"其中之一
    """
    ERR_CODE = 0x006

    def __init__(self, robot_code, version, model_type, reason="unknown"):
        self.robot_code = robot_code
        self.version = version
        self.model_type = model_type
        self.reason = reason

    def err_msg(self):
        msg = "模型加载失败，请确认训练数据或配置格式，并重新训练模型\n"
        msg += "robot_code: {}\n".format(self.robot_code)
        msg += "version: {}\n".format(self.version)
        msg += "model_type: {}\n".format(self.model_type)
        msg += "reason: {}\n".format(self.reason)
        return msg


class DialogueRuntimeException(XiaoYuBaseException):
    """
    当运行对话流程时，由于配置不符合某些规则造成的错误引发的异常
    """
    ERR_CODE = 0x007

    def __init__(self, reason, robot_code, node_name):
        self.reason = reason
        self.robot_code = robot_code
        self.node_name = node_name

    def err_msg(self):
        msg = "对话流程配置异常，请检查对话流程配置"
        msg += "reason: {}\n".format()
        msg += "robot_code: {}\n".format(self.robot_code)
        msg += "node_name: {}\n".format(self.node_name)
        return msg


class RobotNotFoundException(XiaoYuBaseException):
    """创建会话过程中没有找到对应可用机器人时会抛出此异常
    """
    ERR_CODE = 0x008

    def __init__(self, robot_code):
        self.robot_code = robot_code

    def err_msg(self):
        msg = "没有找到机器人{}".format(self.robot_code)
        return msg


class ModelTypeException(XiaoYuBaseException):
    """执行push、checkout等方法时一般要求指定模型类型
       模型类型定义在 utils.define.MODEL_TYPE_*
       当指定这三种类型之外的值时，将抛出该异常
    """

    def __init__(self, model_type):
        self.model_type = model_type

    def err_msg(self):
        return "指定模型类型错误，不存在{}类型".format(self.model_type)


class MethodNotAllowException(XiaoYuBaseException):
    """
    web api请求的方法不存在时抛出的异常
    """
    ERR_CODE = 0x009

    def __init__(self, method, allowed):
        self.method = method
        self.allowed = allowed

    def err_msg(self):
        return "不存在该方法（method）{}，允许的方法有{}".format(self.method, self.allowed)
