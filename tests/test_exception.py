import pytest
from rest_framework.test import  APIClient
from app01 import models
#异常测试
#不存在员工测试
@pytest.mark.django_db
def test_account_get_notexistent_employee():
    account=models.Account.objects.create(
        username="pytest_notexists",
        password="123456"
    )

    client=APIClient()
    session=client.session
    session["info"]={
        "account_id":account.id,
        "username":account.username
    }
    session.save()

    response=client.get("/api/v2/employees/99999/")

    print("status_code=",response.status_code)
    print("response=",response.data)

    assert response.status_code == 404

#缺少必要字段的测试
@pytest.mark.django_db
def test_account_create_employee_with_missing_fields():
    account=models.Account.objects.create(
        username="pytest_account",
        password="123456"
    )
    client=APIClient()
    session=client.session
    session["info"]={
        "account_id":account.id,
        "username":account.username
    }
    session.save()

    response=client.post(
        "/api/v2/employees/",
        {
            "name":"测试员工"
        },
        format="json"
    )

    print("status_code=",response.status_code)
    print("response=",response.data)

    assert response.status_code == 400