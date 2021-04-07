# 小语对话工厂实例
本项目为小语对话工厂的单服务实例，可多开扩展。

## 快速开始
项目依赖
- Linux
- python3.7
- pip

安装项目依赖包

```
pip install -i https://mirrors.aliyun.com/pypi/simple -r requirements.txt
```


创建工作目录并修改配置文件

```bash
mkdir mount  # 创建工作目录
cd mount
cp ../config.template.yaml config.yaml  # 创建项目运行配置文件
```

根据你的需求修改config.yaml，具体参考[项目配置](doc/项目配置.md)


运行服务

```
python run.py
```

测试服务的运行情况

```
PYTHONPATH="./:$PYTHONPATH" python tests/test_chat_api.py
```

## 容器化部署
构建镜像
```
docker build -f deploy/Dockerfile -t xiaoyu:latest .
```
根据*快速开始*章节的内容创建工作目录，修改配置文件

运行容器
```
docker run --name xiaoyu_instance -v /path/to/mount:/root/XiaoyuInstance/mount -p {任意端口}:80 --rm  xiaoyu:latest
```

## 接口文档

- [算法平台训练接口-FAQ](docs/算法平台训练接口-FAQ.md)
- [算法平台训练接口-多轮](docs/算法平台训练接口-多轮.md)
- [算法平台-对话接口](docs/算法平台-对话接口.md)
- [算法平台-系统级接口](docs/算法平台-系统接口.md)
- [小语对话工厂SDK接入文档](docs/小语对话工厂SDK接入文档.md)

