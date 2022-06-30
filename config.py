"""
读取项目配置文件
"""
import os
import yaml
from multiprocessing import Queue

global_config = {
    "serve_port": 80,
    "faq_engine_addr": None,
    "model_storage_folder": "mount/models",
    "graph_storage_folder": "mount/dialogue_graph",
    "log_dir": "mount/logs",
    "external_xiaoyu_ip": None,
    "external_xiaoyu_port": None,
    "master_addr": "",  # 如果此节点是测试节点，该参数指定主节点的位置
    "source_root": os.path.dirname(os.path.abspath(__file__)),
    "conversation_expired_time": 10 * 60,  # 会话过期时间
    # 是否延迟加载机器人模型，内部参数，配置文件中不要设置
    "_delay_loading_robot": False,
    "sentiment_server_url": "",  # 情感分析接口地址
    "project_name": "_default",  # 部署项目名，项目hardcoding的部分可以柑橘项目名称进行选择
    "chitchat_server_addr": "",  # 闲聊服务地址
    # mysql 相关配置
    "db_host": "",
    "db_port": 3306,
    "db_user": "",
    "db_password": "",
    "db_name": "yuyitech_platform",
}

# 源代码根目录
source_root = os.path.abspath(os.path.dirname(__file__))

if not os.path.exists("mount/config.yaml"):
    # 如果配置文件不存在，则从环境变量加载配置
    envs = {key: os.environ[key] for key in global_config if key in os.environ}
    global_config.update(envs)
else:
    with open("mount/config.yaml", "r") as f:
        global_config.update(yaml.load(f.read()))

empty_values = [key for key in global_config if global_config[key] is None]
if empty_values:
    raise AttributeError("These paramater must be set by config file "
                         "or enviroment variables. {}".format(empty_values))
global_queue = Queue()

DATABASE_CONFIG = {
    "host": global_config["db_host"],
    "port": int(global_config["db_port"]),
    "db": global_config["db_name"],
    "user": global_config["db_user"],
    "password": global_config["db_password"],
    "charset": "utf8",
}
