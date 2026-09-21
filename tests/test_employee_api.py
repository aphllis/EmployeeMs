import pytest
from rest_framework.test import APIClient
from app01 import models

# Employee员工 CRUD测试
# POST 测试
@pytest.mark.django_db
def test_admin_can_create_employee():
    # 创建管理员
    admin = models.Admin.objects.create(
        username="pytest_admin_create", password="123456"
    )

    # 创建部门
    department = models.Department.objects.create(title="测试部")

    # 创建api client
    client = APIClient()

    # 模拟管理员登录
    session = client.session
    session["info"] = {
        "id": admin.id,
        "username": admin.username,
    }
    session.save()

    # post 创建员工
    response = client.post(
        "/api/v2/employees/",
        {
            "name": "测试员工",
            "password": "123456",
            "age": 30,
            "account": "1000.00",
            "entrytime": "2026-09-21",
            "depart": department.id,
            "gender": 1,
        },
        format="json",
    )

    print("status_code=", response.status_code)
    print("status", response.data)

    assert response.status_code == 201

    employee = models.Employee.objects.get(name="测试员工")

    assert employee.age == 30
    assert employee.account == 1000
    assert employee.depart_id == department.id
    assert employee.gender == 1


# GET 测试 独立测试单独创建员工，不依赖POST测试
@pytest.mark.django_db
def test_admin_can_get_employee_list():
    # 1.创建管理员
    admin = models.Admin.objects.create(username="pytest_admin_list", password="123456")

    # 2.创建部门
    department = models.Department.objects.create(
        title="测试部门",
    )

    # 3.准备两条员工数据
    models.Employee.objects.create(
        name="张三",
        password="123456",
        age=28,
        account=1000,
        entrytime="2026-09-01",
        depart=department,
        gender=1,
    )
    models.Employee.objects.create(
        name="李四",
        password="123456",
        age=30,
        account=1000,
        entrytime="2026-09-01",
        depart=department,
        gender=2,
    )

    # 4.创建api client
    client = APIClient()

    # 5.模拟管理员登录
    session = client.session
    session["info"] = {"id": admin.id, "username": admin.username}

    session.save()

    # 6.GET 员工列表
    response = client.get("/api/v2/employees/")

    print("status_code=", response.status_code)
    print("response=", response.data)

    # 7.验证HTTP验证码
    assert response.status_code == 200

    # 8.验证返回数量
    assert response.data["count"] == 2

    # 9.验证返回员工
    names = [ item["name"] for item in response.data["results"]]

    assert "张三" in names
    assert "李四" in names

# GET 测试，获取具体某个员工的信息
@pytest.mark.django_db
def test_admin_can_get_employee_detail():

    admin=models.Admin.objects.create(
        username="pytest_admin",
        password="123456"
    )

 
    department=models.Department.objects.create(
        title="测试部门"
    )
  
    employee=models.Employee.objects.create(
        name="王五",
        password="123456",
        age=32,
        account=2000,
        entrytime="2026-09-21",
        depart=department,
        gender=1,
    )

    client=APIClient()
    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()

    response=client.get(
        f"/api/v2/employees/{employee.id}/"
    )

    print("status_code=",response.status_code)
    print("response=",response.data)

    assert response.status_code ==200
    assert response.data["name"] == "王五"
    assert response.data["age"] == 32
    assert response.data["account"] == "2000.00"
    assert response.data["entrytime"] == "2026-09-21"
    assert response.data["depart"] == department.id
    assert response.data["gender"] == 1

#PATCH 测试
@pytest.mark.django_db
def test_admin_can_update_employee():
    admin=models.Admin.objects.create(
        username="pytest_admin_patch",
        password="123456"
    )

    department=models.Department.objects.create(
        title="测试部门"
    )
    employee=models.Employee.objects.create(
        name="王五",
        password="123456",
        age=32,
        account=2000,
        entrytime="2026-09-21",
        depart=department,
        gender=1,
    )

    client=APIClient()
    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()

    response=client.patch(
        f"/api/v2/employees/{employee.id}/",
        {
            "age":35,
            "account":5000,
        },
        format="json"
    )

    print("status_code=",response.status_code)
    print("response=",response.data)

    assert response.status_code==200

    assert response.data["name"] == "王五"
    assert response.data["age"] == 35
    assert response.data["account"] == "5000.00"

    employee.refresh_from_db()

    assert employee.age==35
    assert response.data["account"] == "5000.00"


#DELETE 测试
@pytest.mark.django_db
def test_admin_can_delete_employee():
    admin=models.Admin.objects.create(
        username="pytest_admin_delete",
        password="123456"
    )

    department=models.Department.objects.create(
        title="测试部门"
    )

    employee=models.Employee.objects.create(
        name="waitfordelete",
        password="123456",
        age=30,
        account=1000,
        entrytime="2026-09-03",
        depart=department,
        gender=1,
    )

    employee_id=employee.id

    client=APIClient()

    session=client.session
    session["info"]={
        "id":admin.id,
        "username":admin.username
    }
    session.save()

    #delete请求
    response=client.delete(
        f"/api/v2/employees/{employee_id}/"
    )

    print("status_code=",response.status_code)
    print("response=",response.data  if response.data else None)

    #成功删除后no content 返回204
    assert response.status_code==204

    #数据库确认该员工不存在
    assert not models.Employee.objects.filter(id=employee_id).exists()



