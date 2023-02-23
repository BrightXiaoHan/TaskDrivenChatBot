"""Setup Scripts for the Python Package."""
from setuptools import find_packages, setup

install_requires = [
    "fastapi",
    "typer",
    "sqlmodel",
    "uvicorn",
    "pydantic",
    "pypinyin",
    "pymysql",
    "jieba",
    "aiohttp",
    "strsimpy",
    "ngram",
    "dimsim",
    "elasticsearch",
    "more_itertools",
    "toolz",
    "opencc",
    "spacy",
    "cpca",
    "pyunit_time",
    "cn2an",
]

setup(
    name="xiaoyu",
    version="2.0",
    author="hanbing",
    author_email="beatmight@gmail.com",
    description="Task Driven Chatbot '小语（XiaoYu）'",
    include_package_data=True,
    url="https://github.com/BrightXiaoHan/TaskDrivenChatBot",
    packages=find_packages(exclude=["test*"]),
    install_requires=install_requires,
    extras_require={
        "test": ["pytest", "locust", "httpretty", "protobuf==3.20.*"],
    },
    entry_points={
        "console_scripts": [
            "xiaoyu=xiaoyu_cli.__main__:main",
        ],
    },
)
