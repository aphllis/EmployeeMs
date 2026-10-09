from app01 import models
from rest_framework import serializers


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Employee
        fields = ["url", "name", "age", "account", "entry_date", "department", "gender"]
        extra_kwargs = {
            "age": {
                "required": True,
                "allow_null": False,
            },
            "entry_date": {
                "required": True,
                "allow_null": False,
            },
            "department": {
                "required": True,
                "allow_null": False,
            },
            "gender": {
                "required": True,
                "allow_null": False,
            },
        }


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = ["url", "title"]
