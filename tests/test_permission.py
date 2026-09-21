import pytest
from rest_framework.test import  APIRequestFactory
from app01 import models
from app01 import permissions
# 权限测试，普通员工和管理员区分
@pytest.mark.django_db
def test_employee_is_not_admin():
    employee = models.Employee.objects.create(
        name="普通员工",
        password="123456",
        age=30,
        account=1000,
        entrytime="2026-09-05",
        depart=models.Department.objects.create(title="测试部门"),
        gender=1,
    )
    factory=APIRequestFactory()
    request=factory.get("/api/v2/epmployees/")
    request.user=employee
    permission=permissions.IsAdmin()

    assert permission.has_permission(
        request,None
    ) is False