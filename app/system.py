from app.base import _BaseHandler
from backend import delete, push, cluster

__all__ = ["PushHandler", "DeleteHandler", "ClusterHandler"]


class PushHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        version = kwargs["version"]
        return await push(robot_code, version)


class DeleteHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return delete(robot_code)


class ClusterHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return cluster(robot_code)
