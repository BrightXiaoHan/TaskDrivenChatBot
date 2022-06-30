from app.base import BaseHandler
from backend import analyze, session_reply
from utils.define import FAQ_DEFAULT_PERSPECTIVE

__all__ = ["ReplySessionHandler", "NLUHandler"]


class ReplySessionHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robotId"]
        session_id = kwargs["sessionId"]
        user_says = kwargs["userSays"]
        user_code = kwargs.get("userCode", "")
        params = kwargs.get("params", {})
        recommend_num = kwargs.get("recommend_num", 5)
        perspective = kwargs.get("perspective", FAQ_DEFAULT_PERSPECTIVE)
        rcm_threshold = kwargs.get("rcm_threshold", -1)
        ans_threshold = kwargs.get("ans_threshold", -1)
        traceback = kwargs.get("traceback", False)
        dialogue_type = kwargs.get("type", "text")
        flow_id = kwargs.get("flowId", None)

        faq_params = {
            "recommend_num": recommend_num,
            "perspective": perspective,
            "dialogue_type": dialogue_type,
        }

        if rcm_threshold > 0:
            faq_params["rcm_threshold"] = rcm_threshold
        if ans_threshold > 0:
            faq_params["ans_threshold"] = ans_threshold

        return await session_reply(
            robot_code,
            session_id,
            user_says,
            user_code,
            params,
            faq_params,
            traceback=traceback,
            flow_id=flow_id,
        )


class NLUHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        text = kwargs["text"]

        return await analyze(robot_code, text)
