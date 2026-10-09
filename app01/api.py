import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app01 import models


MAX_PAGE_SIZE = 100


def _error(message, status=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return JsonResponse(payload, status=status)


def _json_body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        raise ValueError("请求体必须是有效的 JSON")
    if not isinstance(data, dict):
        raise ValueError("请求体必须是 JSON 对象")
    return data


def _pagination(request, queryset):
    try:
        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("page_size", 20)), 1), MAX_PAGE_SIZE)
    except ValueError:
        raise ValueError("page 和 page_size 必须是正整数")

    total = queryset.count()
    start = (page - 1) * page_size
    return queryset[start:start + page_size], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
    }


def _department_data(department):
    return {"id": department.id, "title": department.title}


def _employee_data(employee):
    return {
        "id": employee.id,
        "name": employee.name,
        "age": employee.age,
        "entry_date": employee.entry_date.isoformat(),
        "gender": employee.gender,
        "gender_display": employee.get_gender_display(),
        "department": {
            "id": employee.department_id,
            "title": employee.department.title,
        },
    }


def _required(data, fields):
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"缺少必填字段: {', '.join(missing)}")


def _employee_values(data, partial=False):
    fields = ("name", "age", "entry_date", "department_id", "gender")
    if not partial:
        _required(data, fields)
    values = {}
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValueError("name 必须是非空字符串")
        values["name"] = data["name"].strip()
    for field in ("age", "department_id", "gender"):
        if field in data:
            try:
                values[field] = int(data[field])
            except (TypeError, ValueError):
                raise ValueError(f"{field} 必须是整数")
    if "entry_date" in data:
        try:
            values["entry_date"] = date.fromisoformat(data["entry_date"])
        except (TypeError, ValueError):
            raise ValueError("entry_date 必须是 YYYY-MM-DD 格式")
    if "password" in data:
        if not isinstance(data["password"], str) or not data["password"]:
            raise ValueError("password 必须是非空字符串")
        values["password"] = data["password"]
    return values


@csrf_exempt
def department_api(request, department_id=None):
    if request.method == "GET":
        if department_id is not None:
            department = models.Department.objects.filter(id=department_id).first()
            return (_error("部门不存在", 404) if department is None
                    else JsonResponse({"data": _department_data(department)}))
        queryset = models.Department.objects.order_by("id")
        title = request.GET.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)
        try:
            rows, pagination = _pagination(request, queryset)
        except ValueError as exc:
            return _error(str(exc))
        return JsonResponse({
            "data": [_department_data(row) for row in rows],
            "pagination": pagination,
        })

    if department_id is not None:
        department = models.Department.objects.filter(id=department_id).first()
        if department is None:
            return _error("部门不存在", 404)
        if request.method == "POST":
            return _error("详情地址不支持 POST", 405)
    elif request.method == "POST":
        department = None
    else:
        return _error("该方法需要部门 ID", 405)

    try:
        data = _json_body(request)
        if request.method == "POST":
            _required(data, ("title",))
            department = models.Department(title=data["title"])
        elif request.method in ("PUT", "PATCH"):
            if "title" not in data:
                return _error("缺少必填字段: title")
            department.title = data["title"]
        else:
            department.delete()
            return HttpResponse(status=204)
        if not isinstance(department.title, str) or not department.title.strip():
            return _error("title 必须是非空字符串")
        department.title = department.title.strip()
        department.full_clean()
        department.save()
    except (ValueError, ValidationError) as exc:
        return _error(str(exc))
    except IntegrityError:
        return _error("部门保存失败", 409)
    return JsonResponse({"data": _department_data(department)},
                        status=201 if request.method == "POST" else 200)


@csrf_exempt
def employee_api(request, employee_id=None):
    if request.method == "GET":
        if employee_id is not None:
            employee = models.Employee.objects.select_related("department").filter(
                id=employee_id
            ).first()
            return (_error("员工不存在", 404) if employee is None
                    else JsonResponse({"data": _employee_data(employee)}))
        queryset = models.Employee.objects.select_related("department").order_by("id")
        name = request.GET.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        department_id = request.GET.get("department_id")
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        try:
            rows, pagination = _pagination(request, queryset)
        except ValueError as exc:
            return _error(str(exc))
        return JsonResponse({
            "data": [_employee_data(row) for row in rows],
            "pagination": pagination,
        })

    if employee_id is not None:
        employee = models.Employee.objects.filter(id=employee_id).first()
        if employee is None:
            return _error("员工不存在", 404)
        if request.method == "POST":
            return _error("详情地址不支持 POST", 405)
    elif request.method == "POST":
        employee = None
    else:
        return _error("该方法需要员工 ID", 405)

    try:
        data = _json_body(request)
        values = _employee_values(data, partial=request.method == "PATCH")
        if request.method == "POST":
            _required(data, ("password",))
            employee = models.Employee(**values)
        elif request.method in ("PUT", "PATCH"):
            for field, value in values.items():
                setattr(employee, field, value)
        else:
            employee.delete()
            return HttpResponse(status=204)
        employee.full_clean()
        employee.save()
    except (ValueError, ValidationError) as exc:
        details = exc.message_dict if isinstance(exc, ValidationError) else None
        return _error("员工数据校验失败" if details else str(exc), details=details)
    except IntegrityError:
        return _error("员工保存失败，请确认部门存在", 409)
    employee = models.Employee.objects.select_related("department").get(id=employee.id)
    return JsonResponse({"data": _employee_data(employee)},
                        status=201 if request.method == "POST" else 200)
