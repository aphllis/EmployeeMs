import pytest
from rest_framework.test import APIClient
from app01 import models

# Employee员工 CRUD测试
# POST 测试
@pytest.mark.django_db
def test_admin_can_create_department():
    # 创建管理员
    admin = models.Admin.objects.create(
        username="pytest_admin_create", password="123456"
    )

    # 创建api client
    client = APIClient()

    # 模拟管理员登录
    session = client.session
    session["info"] = {
        "id": admin.id,
        "username": admin.username,
    }
    session.save()

    # post 创建部门
    response = client.post(
        "/api/v2/departments/",
        {
            "title":"测试部"
        },
        format="json",
    )

    print("status_code=", response.status_code)
    print("status", response.data)

    #201 created
    assert response.status_code == 201

    department=models.Department.objects.filter(title="测试部").exists()

    assert department is True


# GET 测试 
@pytest.mark.django_db
def test_admin_can_get_department_list():

    admin = models.Admin.objects.create(username="pytest_admin_list", password="123456")

    department = models.Department.objects.create(
        title="测试部门",
    )

    client = APIClient()

    session = client.session
    session["info"] = {"id": admin.id, "username": admin.username}

    session.save()

    response = client.get("/api/v2/departments/")

    print("status_code=", response.status_code)
    print("response=", response.data)

    assert response.status_code == 200

    assert response.data["count"] == 1

    titles = [ item["title"] for item in response.data["results"]]

    assert "测试部门" in titles

# GET 测试，获取具体部门的信息
@pytest.mark.django_db
def test_admin_can_get_department_detail():

    admin=models.Admin.objects.create(
        username="pytest_admin",
        password="123456"
    )

 
    department=models.Department.objects.create(
        title="测试部门"
    )

    client=APIClient()
    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()

    response=client.get(
        f"/api/v2/departments/{department.id}/"
    )

    print("status_code=",response.status_code)
    print("response=",response.data)

    assert response.status_code ==200
    assert response.data["title"] == "测试部门"


#PATCH 测试
@pytest.mark.django_db
def test_admin_can_update_department():
    admin=models.Admin.objects.create(
        username="pytest_admin_patch",
        password="123456"
    )
    department=models.Department.objects.create(
        title="测试部门"
    )
    client=APIClient()
    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()
    response=client.patch(
        f"/api/v2/departments/{department.id}/",
        {
            "title":"研发部门"
        },
        format="json"
    )
    print("status_code=",response.status_code)
    print("response=",response.data)
    assert response.status_code==200
    assert response.data["title"] == "研发部门"

    department.refresh_from_db()
    assert response.data["title"] == "研发部门"


#DELETE 测试
@pytest.mark.django_db
def test_admin_can_delete_department():
    admin=models.Admin.objects.create(
        username="pytest_admin_delete",
        password="123456"
    )

    department=models.Department.objects.create(
        title="测试部门"
    )

    department_id=department.id

    client=APIClient()

    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()

    #delete请求
    response=client.delete(
        f"/api/v2/departments/{department_id}/"
    )

    print("status_code=",response.status_code)
    print("response=",response.data  if response.data else None)

    #成功删除后no content 返回204
    assert response.status_code==204

    #数据库确认该员工不存在
    assert not models.Employee.objects.filter(id=department_id).exists()



