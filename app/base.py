import json
import logging
import traceback

from tornado.web import RequestHandler

from utils.exceptions import EXCEPTION_LOGGER, XiaoYuBaseException

logger = logging.getLogger("Service")


class BaseHandler(RequestHandler):
    def options(self):
        self.set_status(204)
        self.finish()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS"
        )
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Expose-Headers", "Content-Type")

    async def post(self):

        response_dict = {
            "code": 200,
            "msg": "请求成功",
        }
        try:
            params = json.loads(self.request.body)
            logger.info("收到json数据：%s" % json.dumps(params, ensure_ascii=False))
            response_dict["data"] = await self._get_result_dict(**params)
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
