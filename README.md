##  快速开始

### 1. 环境准备

确保您的系统中已安装 Python 3.10+ 和 MySQL

### 2. 克隆与安装

```

### REST API

项目提供不依赖第三方包的 JSON API，统一前缀为 `/api/v1/`。列表接口支持
`page`、`page_size`（最大 100）分页参数。

API 使用项目现有的 Session 登录态，未登录请求返回 `401` JSON 响应；请先通过
`/login/` 登录并携带同一个 Session Cookie。

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| GET/POST | `/api/v1/departments/` | 部门列表 / 创建部门 |
| GET/PUT/PATCH/DELETE | `/api/v1/departments/<id>/` | 部门详情及修改 |
| GET/POST | `/api/v1/employees/` | 员工列表 / 创建员工 |
| GET/PUT/PATCH/DELETE | `/api/v1/employees/<id>/` | 员工详情及修改 |

员工列表还支持 `name` 和 `depart_id` 筛选。创建员工时需要提供
`name`、`password`、`age`、`entrytime`（`YYYY-MM-DD`）、`depart_id` 和
`gender`；响应不会返回密码字段。新增和修改请求的 `Content-Type` 应为
`application/json`。bash
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