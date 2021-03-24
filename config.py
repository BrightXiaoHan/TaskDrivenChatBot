"""
读取项目配置文件
"""
import os
import yaml
from multiprocessing import Queue

global_config = {
    "serve_port": 80,
    "log_dir": "mount/logs",
    "source_root": os.path.dirname(os.path.abspath(__file__)),
    "conversation_expired_time": 10 * 60  # 会话过期时间
}

with open("mount/config.yaml", "r") as f:
    global_config.update(yaml.load(f.read()))

global_queue = Queue()
