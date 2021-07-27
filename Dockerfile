ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}

ARG SOURCE_DIR=/root/XiaoyuInstance
# 安装Python依赖库
WORKDIR ${SOURCE_DIR}

ADD requirements.txt .
ADD deploy deploy
ADD assets assets

RUN python3 -m pip --no-cache-dir install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple && \
    tar -zvxf assets/zh_core_web_sm.tar.gz -C assets && \
    python3 deploy/preload.py && \
    python3 deploy/train_empty_nlu_model.py

# 添加源码，并训练nlu模型
WORKDIR ${SOURCE_DIR}
ADD . ${SOURCE_DIR}

EXPOSE 80
CMD [ "python", "run.py" ]