from app.base import _BaseHandler
from app.executor import send_train_task
from backend import checkout, graph_train, nlu_train
from utils.define import MODEL_TYPE_NLU, MODEL_TYPE_DIALOGUE
from utils.exceptions import MethodNotAllowException

__all__ = ["NLUHandler", "GraphHandler"]


class NLUHandler(_BaseHandler):

    async def _get_result_dict(self, **kwargs):
        method = kwargs["method"]
        robot_code = kwargs["robot_id"]
        version = kwargs["version"]
        data = kwargs.get("data", None)
        if method == "train":
            # 这里如果是push过来的数据的话，需要解析convert参数
            _convert = kwargs.get("_convert", True)
            response_data = nlu_train(robot_code, version, data, _convert)
            send_train_task(robot_code, version)
            return response_data
        elif method == "checkout":
            return checkout(robot_code, MODEL_TYPE_NLU, version)
        else:
            raise MethodNotAllowException(method, "train, checkout")


class GraphHandler(_BaseHandler):

    async def _get_result_dict(self, **kwargs):
        method = kwargs["method"]
        robot_code = kwargs["robot_id"]
        version = kwargs["version"]
        data = kwargs.get("data", None)
        if method == "train":
            return graph_train(robot_code, version, data)
        elif method == "checkout":
            return checkout(robot_code, MODEL_TYPE_DIALOGUE, version)
        else:
            raise MethodNotAllowException(method, "train, checkout")
