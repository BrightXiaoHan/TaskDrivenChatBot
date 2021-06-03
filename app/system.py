from app.base import _BaseHandler
from backend import push, delete

__all__ = ["PushHandler", "DeleteHandler"]


class PushHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        robot_code = kwargs['robot_id']
        version = kwargs['version']
        return push(robot_code, version)


class DeleteHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        robot_code = kwargs['robot_id']
        return delete(robot_code)
