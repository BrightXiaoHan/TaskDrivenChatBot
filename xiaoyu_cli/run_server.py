"""服务启动入口."""
import fastapi
import typer
import uvicorn

from xiaoyu.config import read_config
from xiaoyu.utils.logging import get_logger


def main(config_path: str = typer.Argument(..., help="配置文件路径")):
    """服务启动入口函数."""

    config = read_config(config_path)
    global app
    global logger
    app = fastapi.FastAPI()
    logger = get_logger("xiaoyu", elk_host=config.elk_host, elk_port=config.elk_port)
    uvicorn.run(app, host="0.0.0.0", port=config.server_port)


@app.post("/xiaoyu/faq")
async def faq():
    pass


@app.post("/xiaoyu/faq/chitchat")
async def chitchat():
    pass


@app.post("/xiaoyu/multi/nlu")
async def nlu():
    pass


@app.post("/xiaoyu/multi/graph")
async def graph():
    pass


@app.post("/xiaoyu/push")
async def push():
    pass


@app.post("/xiaoyu/delete")
async def delete():
    pass


@app.post("/xiaoyu/delete/graph")
async def delete_graph():
    pass


@app.post("/api/v1/session/reply")
async def reply_session():
    pass


@app.post("/xiaoyu/analyze")
async def analyze():
    pass


@app.post("/xiaoyu/cluster")
async def cluster():
    pass


@app.post("/xiaoyu/sensitive_words")
async def sensitive_words():
    pass


@app.post("/xiaoyu/sensitive_words/train")
async def sensitive_words_train():
    pass


@app.post("/xiaoyu/multi/qadb")
async def dynamic_qa_train():
    pass


@app.post("/xiaoyu/multi/intentdb")
async def dynamic_intent_train():
    pass


if __name__ == "__main__":
    typer.run(main)
