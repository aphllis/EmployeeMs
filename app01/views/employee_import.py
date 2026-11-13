from datetime import datetime, date
import uuid
import secrets
import time

from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from openpyxl import load_workbook, Workbook

from app01 import models
from app01.utils.permission import account_permission

HEADERS = [
    "工号",
    "姓名",
    "性别",
    "年龄",
    "入职日期",
    "部门",
    "职位",
    "登录用户名",
]
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 500


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _parse_gender(value):
    value = _text(value)
    if not value:
        return None
    if value in ("男", "1"):
        return 1
    if value in ("女", "2"):
        return 2
    raise ValueError("性别请填写“男”或“女”")


def _parse_age(value):
    if value is None or _text(value) == "":
        return None
    # 先转换成浮点形式，然后用is_integer()判断避免类似"30.5"的输入
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("年龄必须是整数")

    if not number.is_integer() or number < 1 or number > 150:
        raise ValueError("年龄必须是 1 到 150 之间的整数")

    return int(number)


def _parse_entry_date(value):
    if value is None or _text(value) == "":
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    try:
        return date.fromisoformat(_text(value)).isoformat()
    except ValueError:
        raise ValueError("入职日期请使用 YYYY-MM-DD 格式")


def _read_employee_rows(file_obj):
    """
    读取上传的EXCEL员工表，检查表头的每行数据，整理正确的行成可用格式，收集错误
    函数返回为preview_rows, row_errors, global_error
    preview_rows：校验通过的数据，供前端预览。
    row_errors：具体哪些 Excel 行有错误、错误原因是什么。
    global_error：整个文件无法继续处理时的错误，例如缺少表头或员工行数超过上限。
    """
    # load_workbook 用来读取xlsx文件的方法
    # data_only 读取公式计算结果而不是公式本身
    workbook = load_workbook(file_obj, read_only=True, data_only=True)
    try:
        # 读取第一张工作表
        sheet = workbook.worksheets[0]
        header_values = next(
            # value_only表示只读取单元格值，不返回完整单元格对象
            sheet.iter_rows(min_row=1, max_row=1, values_only=True),
            None,
        )
        if not header_values:
            return [], [], "Excel 文件没有表头"

        headers = [_text(value) for value in header_values]

        if len(headers) != len(set(headers)):
            return [], [], "Excel 表头有重复列"

        missing_headers = [header for header in HEADERS if header not in headers]
        if missing_headers:
            return [], [], f"缺少表头:{','.join(missing_headers)}"

        # 表头列字典
        header_index = {header: index for index, header in enumerate(headers)}

        # 部门与部门名字典
        departments_by_title = {}
        for department in models.Department.objects.filter(is_active=True):
            departments_by_title.setdefault(department.title, []).append(department)

        # 职位与(部门id,职位名)字典
        positions_by_department_and_name = {}
        positions = models.Position.objects.filter(
            is_active=True, department__is_active=True
        ).select_related("department")

        for position in positions:
            key = (position.department_id, position.name.strip())
            positions_by_department_and_name.setdefault(key, []).append(position)

        # 所有存在的合法员工工号的集合
        existing_employee_numbers = {
            value.casefold()
            for value in models.Employee.objects.exclude(employee_no__isnull=True)
            .exclude(employee_no="")
            .values_list("employee_no", flat=True)
        }

        # 所有账号名的集合
        existing_usernames = {
            value.casefold()
            for value in models.Account.objects.values_list("username", flat=True)
        }

        seen_employee_numbers = set()
        seen_usernames = set()
        # 保存校验通过的行
        preview_rows = []
        # 保存每个错误行即原因
        row_errors = []
        # 统计非空员工数据行的数量
        data_row_count = 0

        for row_number, values in enumerate(
            sheet.iter_rows(min_row=2, values_only=True), start=2
        ):
            if not any(_text(value) for value in values):
                continue
            data_row_count += 1
            if data_row_count > MAX_IMPORT_ROWS:
                return [], [], f"单次最多导入 {MAX_IMPORT_ROWS} 名员工"

            def cell(header):
                index = header_index[header]
                return values[index] if index < len(values) else None

            errors = []
            employee_no = _text(cell("工号"))
            name = _text(cell("姓名"))
            department_name = _text(cell("部门"))
            position_name = _text(cell("职位"))
            username = _text(cell("登录用户名"))

            # 工号校验
            if not employee_no:
                errors.append("工号不能为空")
            elif len(employee_no) > 32:
                errors.append("工号不能超过32个字符")
            elif employee_no.casefold() in existing_employee_numbers:
                errors.append("工号已存在")
            elif employee_no.casefold() in seen_employee_numbers:
                errors.append("工号在文件中重复")
            else:
                seen_employee_numbers.add(employee_no.casefold())

            # 姓名校验
            if not name:
                errors.append("")
            elif len(name) > 9:
                errors.append("姓名不能超过9个字符")

            # 用户名校验
            if not username:
                errors.append("登录用户名不能为空")
            elif len(username) > 32:
                errors.append("登录用户名不能超过32个字符")
            elif username.casefold() in existing_usernames:
                errors.append("登录用户名已存在")
            elif username.casefold() in seen_usernames:
                errors.append("登录用户名在本文件中重复")
            else:
                seen_usernames.add(username.casefold())

            #  部门名称校验
            department = None
            department_matches = departments_by_title.get(department_name, [])
            if not department_name:
                errors.append("部门不能为空")
            elif len(department_matches) == 0:
                errors.append(f"找不到启用中的部门：{department_name}")
            elif len(department_matches) > 1:
                errors.append(f"部门名称重复，无法确认：{department_name}")
            else:
                department = department_matches[0]

            # 职位校验
            position = None
            if not position_name:
                errors.append("职位不能为空")
            elif department:
                position_matches = positions_by_department_and_name.get(
                    (department.pk, position_name),
                    [],
                )
                if len(position_matches) == 0:
                    errors.append(
                        f"部门“{department_name}”下找不到启用中的职位：{position_name}"
                    )
                elif len(position_matches) > 1:
                    errors.append(
                        f"部门“{department_name}”下职位名称重复：{position_name}"
                    )
                else:
                    position = position_matches[0]

            # 性别，年龄，入职日期解析
            try:
                gender = _parse_gender(cell("性别"))
            except ValueError as exc:
                gender = None
                errors.append(str(exc))

            try:
                age = _parse_age(cell("年龄"))
            except ValueError as exc:
                age = None
                errors.append(str(exc))

            try:
                entry_date = _parse_entry_date(cell("入职日期"))
            except ValueError as exc:
                entry_date = None
                errors.append(str(exc))

            # 收集错误信息字典
            if errors:
                row_errors.append({"row_number": row_number, "errors": errors})
                continue

            # 无错误则正常收集
            preview_rows.append(
                {
                    "employee_no": employee_no,
                    "name": name,
                    "gender": gender,
                    "gender_display": {1: "男", 2: "女"}.get(gender, "—"),
                    "age": age,
                    "entry_date": entry_date or "—",
                    "department_id": department.pk,
                    "department_name": department.title,
                    "position_id": position.pk,
                    "position_name": position.name,
                    "username": username,
                }
            )

        if data_row_count == 0:
            return [], [], "Excel 中没有员工数据"

        # 无全局性错误，返回正常行数据，即错误行的信息
        return preview_rows, row_errors, ""

    # 无论怎样都要关闭workbook
    finally:
        workbook.close()


@account_permission("app01.add_employee")
@account_permission("app01.add_account")
def employee_import_page(req):
    return render(req, "employee_import.html")


@account_permission("app01.add_employee")
@account_permission("app01.add_account")
def employee_import_template(req):
    """设置导入模板，内部包含数据填写表和字段说明表"""
    # Workbook() 是 openpyxl 提供的方法，用来在内存中创建一个新的 Excel 工作簿。
    workbook = Workbook()

    # workbook.active 获取默认的第一个工作表。
    sheet = workbook.active
    # 工作表命名
    sheet.title = "员工导入"
    # 把 HEADERS 中的列名写入第一行，例如工号、姓名、部门、职位等。`append()` 是把一组值依次写成一整行
    sheet.append(HEADERS)

    # 创建一个名为“填写说明”的工作表
    instructions = workbook.create_sheet("填写说明")

    instructions.append(["字段", "说明"])
    instructions.append(["工号", "必填，不能与已有员工重复"])
    instructions.append(["姓名", "必填"])
    instructions.append(["性别", "可填 男、女；也可以留空"])
    instructions.append(["年龄", "可填整数，也可以留空"])
    instructions.append(["入职日期", "格式 YYYY-MM-DD，也可以留空"])
    instructions.append(["部门", "必填，填写系统中已有的启用部门名称"])
    instructions.append(["职位", "必填，填写该部门下已有的启用职位名称"])
    instructions.append(["登录用户名", "必填，不能与已有账号重复"])
    instructions.append(["初始密码", "不要填写；系统会为每个账号生成临时密码"])

    # 创建一个 Django 的 HTTP 响应对象。`content_type` 告诉浏览器，响应内容是 .xlsx 格式的 Excel 文件
    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        )
    )
    # 设置响应头：
    # - attachment 表示把响应当作附件下载；
    # - filename 指定下载文件名为 employee_import_template.xlsx。
    response["Content-Disposition"] = (
        'attachment; filename="employee_import_template.xlsx"'
    )

    # 把刚才在内存中创建的 Excel 文件内容写入 HTTP 响应
    workbook.save(response)
    # 放松HTTP响应对象给浏览器，它会下载
    return response


@require_POST
@account_permission("app01.add_employee")
@account_permission("app01.add_account")
def employee_import_preview(req):
    """
    接收 Excel 文件，检查上传条件并校验文件内容；
    通过后把预览数据暂存在当前登录会话中，再显示预览页面
    """
    file_obj = req.FILES.get("excel_file")

    if not file_obj:
        return render(req, "employee_import.html", {"global_error": "请选择Excel文件"})

    if not file_obj.name.lower().endswith(".xlsx"):
        return render(
            req, "employee_import.html", {"global_error": "目前只支持 .xlsx 文件"}
        )

    if file_obj.size > MAX_FILE_SIZE:
        return render(
            req,
            "employee_import.html",
            {"global_error": "文件不能超过 5 MB"},
        )

    if not Group.objects.filter(name="RegularEmployee").exists():
        return render(
            req,
            "employee_import.html",
            {"global_error": "缺少 RegularEmployee 角色，请先运行 init_rbac"},
        )
    # 读取并校验 Excel 内容
    try:
        preview_rows, row_errors, global_error = _read_employee_rows(file_obj)
    except Exception:
        preview_rows, row_errors = [], []
        global_error = "文件解析失败，请确认文件是有效的 .xlsx 工作簿"

    # 准备交给页面的数据
    context = {
        "preview_rows": preview_rows,
        "row_errors": row_errors,
        "global_error": global_error,
    }

    # 有错误时不生成确认令牌
    if global_error or row_errors:
        return render(req, "employee_import.html", context)

    # 全部通过后，生成预览令牌并暂存数据
    # 生成一个随机令牌，例如一串 32 位的十六进制字符。它用于让确认页面找到这次预览的数据。
    token = uuid.uuid4().hex

    # 把数据放进当前用户的 Django session：
    # - session 的键包含本次预览的令牌；
    # - created_at 记录生成预览的时间，之后可以据此判断预览是否过期；
    # - rows 保存已经校验并整理过的数据。
    # 避免了把全部员工数据放在 HTML 隐藏字段或 URL 中。之后确认导入时，后端根据令牌从 session 取出这些数据。
    req.session[f"employee_import_{token}"] = {
        "created_at": time.time(),
        "rows": preview_rows,
    }

    # 明确告诉 Django 当前 session 已被修改，应该在响应结束时保存;这一行是额外确保保存状态的写法。
    req.session.modified = True

    # 把令牌交给预览页面
    # 将令牌也放进模板上下文，再显示预览页面。模板通常会在确认表单中把它作为隐藏字段提交：
    # <input type="hidden" name="token" value="{{ preview_token }}">
    # 用户点击“确认导入”后，确认视图就能用这个令牌找回 session 中的数据。
    context["preview_token"] = token
    return render(req, "employee_import.html", context)


@require_POST
@account_permission("app01.add_employee")
@account_permission("app01.add_account")
def employee_import_confirm(req):
    """
    确认导入
    从当前会话session中取出预览数据，
    然后创建员工和账号并分配基础角色
    """
    # 获得token令牌
    # 生成session-key
    # 获得预览数据字典
    token = req.POST.get("token", "")
    session_key = f"employee_import_{token}"
    preview_data = req.session.get(session_key)

    if not preview_data:
        return render(
            req,
            "employee_import.html",
            {"global_error": "导入预览已失效，请重新上传文件"},
        )

    if time.time() - preview_data["created_at"] > 30 * 60:
        del req.session[session_key]
        return render(
            req,
            "employee_import.html",
            {"global_error": "预览超过 30 分钟，请重新上传文件"},
        )

    # 一次性显示账号的凭据
    credentials = []

    try:
        # 生成原子事务，同步生效或回滚，账号和员工成对创建
        with transaction.atomic():
            # 从 Django 权限组表中取出 RegularEmployee 角色组
            regular_employee_group = Group.objects.get(name="RegularEmployee")

            # 逐行创建员工
            for row in preview_data["rows"]:
                # 二次校验：预览到确认之间，部门或职位可能已被停用、删除或调整。
                # 根据预览行里的部门 ID 重新查询数据库，并要求部门仍然启用
                department = models.Department.objects.get(
                    pk=row["department_id"],
                    is_active=True,
                )
                # 再查找职位，并同时确认：
                # -职位 ID 与预览时一致；
                # =职位仍属于刚查出的部门；
                # -职位仍然启用。
                position = models.Position.objects.get(
                    pk=row["position_id"],
                    department=department,
                    is_active=True,
                )

                employee = models.Employee.objects.create(
                    employee_no=row["employee_no"],
                    name=row["name"],
                    gender=row["gender"],
                    age=row["age"],
                    # date.fromisoformat将转换成 Python 的日期对象
                    entry_date=(
                        date.fromisoformat(row["entry_date"])
                        if row["entry_date"] != "—"
                        else None
                    ),
                    department=department,
                    position=position,
                )

                temporary_password = secrets.token_urlsafe(9)
                account = models.Account.objects.create(
                    username=row["username"],
                    password=make_password(temporary_password),
                    employee=employee,
                    is_active=True,
                )
                # 把新账号加入 RegularEmployee 角色组
                account.groups.add(regular_employee_group)

                # 收集成功页需要显示的信息
                # 临时密码仅用于稍后的成功页面显示；数据库中保存的仍然是哈希值。
                credentials.append(
                    {
                        "employee_no": employee.employee_no,
                        "name": employee.name,
                        "username": account.username,
                        "temporary_password": temporary_password,
                    }
                )
    # 捕获几种可能的失败：
    # IntegrityError：数据库唯一约束冲突，例如预览之后工号或用户名被其他操作占用；
    # Group.DoesNotExist：普通员工角色组在预览后被删除；
    # Department.DoesNotExist：预览中的部门已经不存在或被停用；
    # Position.DoesNotExist：预览中的职位已经不存在、被停用，或不再属于该部门。
    except (IntegrityError, Group.DoesNotExist,
            models.Department.DoesNotExist, models.Position.DoesNotExist):
        return render(
            req,
            "employee_import.html",
            {
                "global_error": (
                    "导入时数据发生变化或出现重复工号/用户名。"
                    "没有员工被导入，请重新上传并检查数据。"
                )
            },
        )

    # 成功后删除预览数据，并标记 session 已修改。
    del req.session[session_key]
    req.session.modified = True

    # 显示导入成功结果
    return render(
        req,
        "employee_import_result.html",
        {
            "created_count": len(credentials),
            "credentials": credentials,
        },
    )