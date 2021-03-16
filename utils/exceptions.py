class NLUException(Exception):
    """nlu模块基础错误
    """
    pass


class LoadTrainingModelException(NLUException):
    """加载了正在训练中的模型
    """