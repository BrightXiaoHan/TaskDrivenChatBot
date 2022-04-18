ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} as base

RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
    && sed -i s@/security.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list

# 将时区设置为上海
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y tzdata \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*


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

FROM base AS prod
# 添加源码
ADD app app
ADD backend backend
ADD bin bin
ADD external external
ADD tests tests
ADD utils utils
ADD *.py ./

EXPOSE 80
CMD [ "python", "run.py" ]

FROM base AS dev
RUN python3 -m pip --no-cache-dir install ipdb -i https://mirrors.aliyun.com/pypi/simple && \
    apt-get update && \
    apt-get install -y --no-install-recommends vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 80
CMD [ "bash" ]