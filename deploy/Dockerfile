ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}

# 安装Python依赖库
WORKDIR /root
ADD requirements.txt .
RUN python3 -m pip --no-cache-dir install -r requirements.txt -i https://pypi.douban.com/simple

# 添加源码，并训练nlu模型
ARG SOURCE_DIR=/root/XiaoyuInstance
WORKDIR ${SOURCE_DIR}
ADD . ${SOURCE_DIR}

EXPOSE 80
CMD [ "python", "run.py" ]