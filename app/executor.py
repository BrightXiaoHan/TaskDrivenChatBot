import traceback
import logging
from multiprocessing import Process

from config import global_queue, global_config
from backend.nlu import train_robot
from utils.funcs import post_rpc
from utils.define import MODEL_TYPE_NLU
from external import notify_training_complete

__all__ = ["send_train_task", "fork_train_process"]

SERVE_PORT = global_config["serve_port"]


def internal_push_nlu(robot_code, version):
    """通知主进程nlu模型训练完毕，进行版本的切换

    Args:
        robot_code (str): 机器人唯一标识，ID
        version (str): 机器人版本号
    """
    url = "http://localhost:{}/xiaoyu/multi/nlu".format(SERVE_PORT)
    data = {
        "robot_id": robot_code,
        "method": "checkout",
        "version": version
    }
    post_rpc(url, data)


def send_train_task(robot_code, version):
    """向训练守护进程发送训练请求

    Args:
        robot_code (str): 机器人唯一标识
        version (str): 带训练的机器人模型版本
    """
    data = {
        "robot_code": robot_code,
        "version": version,
    }
    global_queue.put_nowait(data)


def fork_train_process():
    """创建守护进程，接收主进程训练消息，存放到队列中，依次对模型进行训练
    """
    logger = logging.getLogger("ProcessTrain")

    def handle_message(msg):
        """处理主进程发送来的消息

        Args:
            msg (dict): 待处理的消息，robot_code，version两个参数
        """
        # 训练nlu模型
        train_robot(**msg)
        # 通知主进程更新模型
        internal_push_nlu(**msg)
        # 通知小语平台训练成功
        notify_training_complete(**msg)

    def consummer():
        """
        队列消费者
        """
        while True:
            msg = global_queue.get()
            try:
                handle_message(msg)
            except Exception:
                logger.error(msg)
                logger.error(traceback.format_exc())

    process = Process(target=consummer)
    process.deamon = True
    process.start()
    return process
