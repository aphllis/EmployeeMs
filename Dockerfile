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
CMD ["python","manage.py","runserver","0.0.0.0:8000"]

# 如果"--noreload"，表示django不自动重载，那么即便有绑定挂载，在修改项目文件时可以同步，但是呈现的效果也是旧的，这一点请牢记
# CMD ["python","manage.py","runserver","0.0.0.0:8000","--noreload"]