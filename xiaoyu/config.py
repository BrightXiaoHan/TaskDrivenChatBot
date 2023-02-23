"""
读取项目配置文件
"""
from typing import Optional

import yaml
from pydantic import BaseModel


class XiaoyuConfig(BaseModel):
    server_port: int = 80
    model_storage_folder: str = "mount/models"
    graph_storage_folder: str = "mount/dialogue_graph"

    log_dir: str = "mount/logs"
    external_xiaoyu_ip: Optional[str] = None
    external_xiaoyu_port: Optional[int] = None
    master_addr: Optional[str] = None  # 如果此节点是测试节点，该参数指定主节点的位置
    conversation_expired_time: int = 10 * 60  # 会话过期时间
    # 是否延迟加载机器人模型，内部参数，配置文件中不要设置
    delay_loading_robot: bool = False
    project_name: str = "xiaoyu"  # 部署项目名，项目hardcoding的部分可以柑橘项目名称进行选择
    # mysql 相关配置
    db_host: Optional[str] = None
    db_port: int = 3306
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: str = "yuyitech_platform"


def read_config(config_file: str) -> XiaoyuConfig:
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    return XiaoyuConfig.parse_obj(config)
