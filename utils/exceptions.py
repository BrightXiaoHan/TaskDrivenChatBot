class XiaoYuBaseException(Exception):
    """
    小语机器人基础异常

    Attributes:
        ERR_CODE (int): 错误码, 需要被子类覆盖
        ERR_MESSAGE (str): 错误描述, 需要被子类覆盖
    """
    ERR_CODE = 0x000
    ERR_MESSAGE = "小语机器人基础异常"

    def log_err(self, logger=None):
        """
        获得需要记录的错误日志
        Args:
            logger(logging.Logger, optional): 输出日志的logger，
                如果不为空直接将logger打印，
                如果为空则只返回需要记录日志的字符串

        Return:
            str: 需要记录到日志的字符串，需要被子类复写
        """
        if logger:
            logger.exception()


class RpcException(XiaoYuBaseException):
    """
    外部请求调用异常

    Atrributes:
        request_url (str): 所请求的服务地址
        request_data (dict): 请求的参数，字典类型的数据
        response_text (str): 服务返回的内容
    """
    ERR_CODE = 0x000
    ERR_MESSAGE = "调用外部服务接口错误"

    def __init__(self, request_url, request_data, response_text, *args):
        super().__init__(*args)
        self.request_url = request_url
        self.request_data = request_data
        self.response_text = response_text

    def log_err(self, logger=None):
        super().log_err(logger)
        log_str = "request url: {}\n".format(self.request_url)
        log_str += "request data: {}\n".format(str(self.request_data))
        log_str += "response_text: {}\n".format(self.response_text)

        if logger:
            logger.error(log_str)
        return log_str


class NLUException(BaseException):
    """nlu模块基础错误
    """
    pass


class LoadTrainingModelException(NLUException):
    """加载了正在训练中的模型
    """
    pass


class DialogueException(BaseException):
    """对话管理模块基础错误
    """
    pass


class ConversationNotFoundException(BaseException):
    """指定的对话id没有找到的错误]
    """
    pass


class NoAvaliableModelException(BaseException):
    """系统启动时没有找到可用的模型，当指定的模型版本不存在时会报此错误
    """
    pass
