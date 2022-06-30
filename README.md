# 小语对话工厂实例
本项目为小语对话工厂的单服务实例，可多开扩展。

## 快速开始
项目依赖
- Linux
- python3.7 (其他python版本没有进行过测试可能会造成错误)
- pip

初始化lfs文件
```
git lfs pull
```

安装项目依赖包

```
pip install -i https://mirrors.aliyun.com/pypi/simple -r requirements.txt
```

解压spacy ner模型
```
tar -zvxf assets/zh_core_web_sm.tar.gz -C assets
```

创建工作目录并修改配置文件

```bash
mkdir mount  # 创建工作目录
cd mount
cp ../config.template.yaml config.yaml  # 创建项目运行配置文件
```

根据你的需求修改config.yaml，具体参考[项目配置](docs/项目配置.md)


运行服务

```
python run.py
```

测试服务的运行情况

```
PYTHONPATH="./:$PYTHONPATH" python tests/test_chat_api.py
```

## 交互测试
如果想单独测试某个机器人的某个版本的模型和配置的话，可以使用交互测试脚本
```
cp bin/params.json.template bin/params.json  # 可以根据需要修改params.json中的数据
PYTHONPATH="./:$PYTHONPATH" python bin/interact.py
```

手动更新对话流程配置可以自动生效，如果手动更新了nlu的训练数据，需要手动重新训练
```
PYTHONPATH="./:$PYTHONPATH" python bin/retrain.py  # 只会训练params.json中指定的机器人和模型版本
```

## 容器化部署
构建镜像
```
docker build -f Dockerfile -t xiaoyu:latest .
```
根据*快速开始*章节的内容创建工作目录，修改配置文件

运行容器
```
docker run --name xiaoyu_instance -v /path/to/mount:/root/XiaoyuInstance/mount -p {任意端口}:80 --rm  xiaoyu:latest
```

## 其他文档
[其他文档](docs)
