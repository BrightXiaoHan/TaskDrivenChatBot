"""Setup Scripts for the Python Package."""
from setuptools import find_packages, setup

install_requires = [
    "fastapi",
    "uvicorn",
    "pydantic",
]

setup(
    name="xiaoyu",
    version="2.0",
    author="hanbing",
    author_email="beatmight@gmail.com",
    description="Task Driven Chatbot '小语（XiaoYu）'",
    include_package_data=True,
    # 项目主页
    url="https://github.com/BrightXiaoHan/TaskDrivenChatBot",
    # 你要安装的包，通过 setuptools.find_packages 找到当前目录下有哪些包
    packages=find_packages(exclude=["test*", "main*"]),
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
