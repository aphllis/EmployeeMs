import pytest
from rest_framework.test import APIClient
from app01 import models



# 未注册登录测试
def test_employee_api_requires_login():
    client = APIClient()

    response = client.get("/api/v2/employees/")

    print("status_code =", response.status_code)
    print("response =", response.data)

    assert response.status_code == 403


# 注册登录测试
@pytest.mark.django_db
def test_admin_can_access_employee_api():
    # 1.创建一个测试管理员
    admin = models.Admin.objects.create(username="pytest_admin", password="123456")

    # 2.创建api客户端
    client = APIClient()

    # 3.模拟django session登录
    session = client.session
    session["info"] = {"id": admin.id, "username": admin.username}
    session.save()

    # 4.请求Employee api
    response = client.get("/api/v2/employees/")

    print("status_code=", response.status_code)
    print("response=", response.data)

    # 5.管理员访问情况判断
    assert response.status_code == 200


# 无效admin登录测试
@pytest.mark.django_db
def test_invalid_admin_session():
    client = APIClient()

    session = client.session
    session["info"] = {"id": 999999, "username": "not_exist"}
    session.save()

    response = client.get("/api/v2/employees/")

    print("status_code=", response.status_code)
    print("response=", response.data)

    assert response.status_code == 403


