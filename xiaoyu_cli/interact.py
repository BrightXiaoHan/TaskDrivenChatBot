"""
交互测试机器人对话情况
"""
import asyncio
import json
from pprint import pprint
from typing import Any, Dict

import typer

from xiaoyu.config import read_config
from xiaoyu.manager import RobotManager


async def run(config_path: str, robot_code: str, graph_id: str, params: Dict[str, Any] = None):
    config = read_config(config_path)
    manager = RobotManager(config)
    sessionId = "test_session"
    user_says = input("用户说：")
    data = await manager.session_reply(
        robot_code=robot_code,
        session_id=sessionId,
        user_says=user_says,
        user_code="user1",
        params=params,
        flow_id=graph_id,
    )
    print("机器人说：{}".format(data["says"]))

    data = None
    while True:
        user_says = input("用户说：")
        if user_says == "info":
            print(manager.agents[params["robot_code"]].user_store[sessionId].latest_msg())
        elif user_says == "verbose":
            pprint(data)
        else:
            data = await manager.session_reply(params["robot_code"], sessionId, user_says)
            print("机器人说：{}".format(data["says"]))


def main(
    config_path: str = typer.Argument(..., help="配置文件路径"),
    robot_code: str = typer.Option(..., help="机器人编码"),
    graph_id: str = typer.Option(None, help="对话流程图配置id"),
    extra_params: str = typer.Option(None, help="额外参数，json字符串格式"),
):
    params = json.loads(extra_params) if extra_params else {}
    asyncio.run(run(config_path, robot_code, graph_id, params))


if __name__ == "__main__":
    typer.run(main)
