import pytest
from rest_framework.test import APIClient

from django.test import Client
from django.contrib.auth.hashers import make_password, check_password

from app01 import models
from app01.utils.encrypt import md5

from tests.helpers import grant_model_permission


# 未注册登录测试
def test_employee_api_requires_login():
    client = APIClient()

    response = client.get("/api/v2/employees/")

    print("status_code =", response.status_code)
    print("response =", response.data)

    assert response.status_code == 403


# 注册登录测试，添加权限测试
@pytest.mark.django_db
def test_account_addperm_can_access_employee_api():
    # 1.创建一个测试管理员
    account = models.Account.objects.create(
        username="pytest_account", password="123456"
    )

    # 2.增加账号权限
    grant_model_permission(account, "employee", "view")

    # 3.创建api客户端
    client = APIClient()

    # 4.模拟django session登录
    session = client.session
    session["info"] = {"account_id": account.pk, "username": account.username}
    session.save()

    # 5.请求Employee api
    response = client.get("/api/v2/employees/")

    # print("status_code=", response.status_code)
    # print("response=", response.data)

    # 5.管理员访问情况判断
    assert response.status_code == 200


# 注册登录测试，未添加权限测试
@pytest.mark.django_db
def test_account_can_access_employee_api():
    # 1.创建一个测试管理员
    account = models.Account.objects.create(
        username="pytest_account", password="123456"
    )

    # 2.创建api客户端
    client = APIClient()

    # 3.模拟django session登录
    session = client.session
    session["info"] = {"account_id": account.pk, "username": account.username}
    session.save()

    # 4.请求Employee api
    response = client.get("/api/v2/employees/")

    # print("status_code=", response.status_code)
    # print("response=", response.data)

    # 5.管理员访问情况判断
    assert response.status_code == 403


# 无效account登录测试
@pytest.mark.django_db
def test_invalid_account_session():
    client = APIClient()

    session = client.session
    session["info"] = {"account_id": 999999, "username": "not_exist"}
    session.save()

    response = client.get("/api/v2/employees/")

    print("status_code=", response.status_code)
    print("response=", response.data)

    assert response.status_code == 403


################### django客户端的密码迁移测试 ####################
@pytest.mark.django_db
def test_legacy_md5_password_auto_migrates(monkeypatch):
    """
    测试旧版md5密码：
    1. 数据库中保存 MD5 密码
    2. 用户使用明文密码登录
    3. 登录成功
    4. 登录成功后自动升级为 Django Password Hash
    """
    # monkeypatch ,由于真实web登录里面用到redis存储验证码，所以用monkeypatch模拟redis的验证码读取

    username = "legacy_account"
    raw_password = "123456"

    old_md5_password = md5(raw_password)

    # 模拟保存旧md5密码
    account = models.Account.objects.create(
        username=username, password=old_md5_password
    )

    # 测试前确认是旧md5
    assert account.password == old_md5_password
    assert len(account.password) == 32

    # djano 测试客户端
    client = Client()

    # 让测试客户端先产生 session_key
    session = client.session
    session.save()
    # 模拟 Redis 中已经存在正确验证码
    monkeypatch.setattr("app01.views.login.client.get", lambda key: "ABCD")
    # POST 登录
    response = client.post(
        "/login/",
        {
            "username": username,
            "password": raw_password,
            "code": "ABCD",
        },
    )
    # 登录成功应该跳转到后台首页
    assert response.status_code == 302
    assert response.url == "/admin/lst/"

    # 重新从数据库读取管理员
    account.refresh_from_db()

    # 密码已经不再是原来的 MD5
    assert account.password != old_md5_password

    # 新密码必须能够被 Django check_password 验证
    assert check_password(raw_password, account.password)

    # 登录后的 session 也应该存在
    session = client.session
    assert session["info"]["account_id"] == account.id
    assert session["info"]["username"] == username


@pytest.mark.django_db
def test_django_hashed_password_login(monkeypatch):
    """
    测试已经是django password hash 管理员
    1. 数据库中保存 Django Hash
    2. 使用正确密码登录
    3. 登录成功
    4. 密码保持原来的 Django Hash
    """
    username = "legacy_account"
    raw_password = "123456"

    django_password = make_password(raw_password)
    account = models.Account.objects.create(username=username, password=django_password)

    assert account.password == django_password
    assert check_password(raw_password, account.password)

    # djano 测试客户端
    client = Client()

    session = client.session
    session.save()

    # 模拟 Redis 中已经存在正确验证码
    monkeypatch.setattr("app01.views.login.client.get", lambda key: "ABCD")

    # POST 登录
    response = client.post(
        "/login/",
        {
            "username": username,
            "password": raw_password,
            "code": "ABCD",
        },
    )
    # 登录成功应该跳转到后台首页
    assert response.status_code == 302
    assert response.url == "/admin/lst/"

    # 重新从数据库读取管理员
    account.refresh_from_db()

    assert account.password == django_password
    assert check_password(raw_password, account.password)

    # 登录后的 session 也应该存在
    session = client.session
    assert session["info"]["account_id"] == account.id
    assert session["info"]["username"] == username


# 测试禁用用户或已删除用户登录
@pytest.mark.django_db
@pytest.mark.parametrize("account_state", ["disabled", "delete"])
def test_api_v2_rejects_disabled_or_deleted_account(account_state):
    account = models.Account.objects.create(
        username=f"api_v2_{account_state}",
        password="unused",
        is_active=True,
    )
    grant_model_permission(account, "employee", "view")
    client = APIClient()
    session = client.session
    session["info"] = {"account_id": account.pk, "username": account.username}
    session.save()

    # 启用状态下，确认这个sessions可以访问api v2
    response = client.get("/api/v2/employees/")
    assert response.status_code == 200

    # 改变数据库里的账号状态，保留客户端原session
    if account_state == "disabled":
        account.is_active = False
        account.save(update_fields=["is_active"])
    else:
        account.delete()

    # 同一session再次请求时应该被拒绝
    response = client.get("/api/v2/employees/")
    assert response.status_code == 403
