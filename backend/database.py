"""
数据库管理机器人模型的相关代码，数据库引擎使用sqlite
"""
import os

from sqlalchemy import (create_engine,
                        Column,
                        Integer,
                        String)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from utils import hash_string

Base = declarative_base()

__all__ = ["RobotMetaManager",
           "STATUS_DONT_NEED_UPDATE",
           "STATUS_NEED_UPDATE_NLU",
           "STATUS_NEED_UPDATE_FLOW",
           "STATUS_NEED_UPDATE_BOTH",
           "MODEL_AVALIABLE",
           "MODEL_UNAVALIABLE",
           "MODEL_NOT_EXIST"]


class RobotModelMeta(Base):
    __tablename__ = "RobotModelMeta"

    robot_id = Column(String(length=50), primary_key=True, comment="机器人唯一标识id")
    corpus_hash = Column(String(length=20),
                         nullable=False, comment="训练数据的hash值")
    flow_hash = Column(String(length=20), nullable=False,
                       comment="对话流程配置的hash值")
    model_path = Column(String, nullable=False, comment="模型路径")
    status = Column(Integer, nullable=False, comment="当前状态, 0为可用状态，-1为不可用状态")


STATUS_DONT_NEED_UPDATE = 0  # 不需要更新模型
STATUS_NEED_UPDATE_NLU = 1  # 只需要重新训练nlu模型
STATUS_NEED_UPDATE_FLOW = 2  # 只需要更新对话流程配置
STATUS_NEED_UPDATE_BOTH = 3  # 两者都需要更新

MODEL_AVALIABLE = 5  # 模型可用
MODEL_UNAVALIABLE = 6  # 模型不可用
MODEL_NOT_EXIST = 7  # 模型不存在


class RobotMetaManager(object):
    """
    机器人模型管理器

    Attribute
    """

    def __init__(self, storage_folder):
        """初始化机器人模型管理器

        Args:
            storage_folder (str): 模型存放路径
        """
        self.storage_folder = storage_folder
        self.db_path = os.path.join("meta.db")

    def _initial_database(self):
        engine = create_engine('sqlite:///{}'.format(self.db_path))
        Base.metadata.create_all(engine)
        self.engine = engine

    def add_robot_model(self, robot_id, corpus_content, flow_content):
        """添加机器人模型的元数据，确认数据库中robot_id不存在才可以使用

        Args:
            robot_id (str): 机器人的唯一id标识
            corpus_content (str): rasa nlu训练数据文本内容
            flow_hash (str): 对话流程配置内容
        """
        pass

    def enable_robot_model(self, robot_id):
        """将机器人模型的状态设置为可用

        Args:
            robot_id (str): 机器人的唯一id标识
        """
        pass

    def disable_robot_model(self, robot_id):
        """将机器人模型的状态设置为不可用

        Args:
            robot_id (str): 机器人的唯一id标识
        """
        pass

    def update_robot_model(self, robot_id, corpus_content=None, flow_content=None):
        """更新机器人模型元数据，该方法会验证corpus_content 与 flow_content的hash值与数据库中的hash值是否一致，如果不一致则会更新hash值，将模型状态置为不可用，并且返回是否需要重新训练

        Args:
            robot_id (str): 机器人的唯一id标识
            orpus_content (str): rasa nlu训练数据文本内容
            flow_hash (str): 对话流程配置内容

        Return:
            int:    STATUS_DONT_NEED_UPDATE = 0  # 不需要更新模型
                    STATUS_NEED_UPDATE_NLU = 1  # 只需要重新训练nlu模型
                    STATUS_NEED_UPDATE_FLOW = 2  # 只需要更新对话流程配置
                    STATUS_NEED_UPDATE_BOTH = 3  # 两者都需要更新
                这四个其中之一
        """
        return 0

    def get_model_status(self, robot_id):
        """获取模型的状态

        Args:
            robot_id (str): 机器人的唯一id标识

        Return:
            int:    MODEL_AVALIABLE = 5  # 模型可用
                    MODEL_UNAVALIABLE = 6  # 模型不可用
                    MODEL_NOT_EXIST = 7  # 模型不存在
                这三个值其中之一
        """
        pass
