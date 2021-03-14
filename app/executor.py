import traceback
import logging
from multiprocessing import Process

from config import global_queue
from backend.nlu import train_robot

__all__ = ["send_train_task", "fork_train_process"]


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
            msg (dict): 待处理的消息
        """
        train_robot(**msg)

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
