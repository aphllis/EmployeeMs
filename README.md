##  快速开始

### 1. 环境准备

确保您的系统中已安装 Python 3.10+ 和 MySQL

### 2. 克隆与安装

```bash
# 克隆项目到本地
git clone https://github.com/aphllis/EmployeeMs
cd EmployeeMs

# 安装依赖
pip install -r requirements.txt
```

### 3. 项目配置

- **数据库**:
  打开 `djangoblog/settings.py` 文件，找到 `DATABASES` 配置项，修改为您的 MySQL 连接信息。

  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'your_db_name',
          'USER': 'your_db_user',
          'PASSWORD': 'your_password',
          'HOST': '127.0.0.1',
          'PORT': 3306,
      }
  }
  ```
  在 MySQL 中创建数据库:
  ```sql
  CREATE DATABASE `EmployeeMS` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

### 4. 初始化数据库

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 运行项目

```bash

# 启动开发服务器
python manage.py runserver