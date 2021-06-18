import json
import traceback
import logging

from concurrent.futures import ThreadPoolExecutor
from tornado.gen import coroutine
from tornado.web import RequestHandler
from tornado.concurrent import run_on_executor
from utils.exceptions import XiaoYuBaseException, EXCEPTION_LOGGER

logger = logging.getLogger("Service")


class _BaseHandler(RequestHandler):

    executor = ThreadPoolExecutor(max_workers=4)

    @run_on_executor
    def _get_result_dict(self, **kwargs):
        raise NotImplementedError

    def options(self):
        self.set_status(204)
        self.finish()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods",
                        "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Expose-Headers", "Content-Type")

    @coroutine
    def post(self):

        logger.info("收到请求：%s" % self.request.body)
        response_dict = {
            "code": 200,
            "msg": "请求成功",
        }
        try:
            params = json.loads(self.request.body)
            logger.info("收到json数据：%s" % str(params))
            response_dict["data"] = yield self._get_result_dict(**params)
        except XiaoYuBaseException as e:
            response_dict["code"] = 500
            response_dict["msg"] = e.err_msg()
            e.log_err()
        except KeyError as e:
            response_dict["code"] = 500
            response_dict["msg"] = "请求参数或者data中缺少参数{}".format(e.args[0])
            EXCEPTION_LOGGER.error(traceback.format_exc())
        except Exception as e:
            response_dict["code"] = 500
            response_dict["msg"] = str(e)
            EXCEPTION_LOGGER.error(traceback.format_exc())

        response = json.dumps(response_dict, ensure_ascii=False)
        logger.info("返回内容：%s" % response)
        self.write(response)
