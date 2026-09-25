FROM python:3.13-slim

WORKDIR /app

#安装mysqlclient 编译所需依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

#单独复制依赖文件，利用docker构建缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#复制项目代码
COPY . .
EXPOSE 8000
CMD ["python","manage.py","runserver","0.0.0.0:8000","--noreload"]