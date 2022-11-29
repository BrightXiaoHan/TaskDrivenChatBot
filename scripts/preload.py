"""
预先加载所有需要从互联网下载的模型，以加快第一次启动服务时的速度
"""
import jieba

jieba.enable_paddle()

