from pathlib import PureWindowsPath, PurePosixPath
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError

# from django.core.validators import RegexValidator
from django.db.models import Q
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import Group

from app01 import models
from app01.utils.bootstrap import BootstrapModelForm, BootstrapForm


class DepartModelForm(BootstrapModelForm):
    title = forms.CharField(label="部门名")

    class Meta:
        model = models.Department
        fields = [
            "code",
            "title",
            "parent",
            "description",
            "sort_order",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["parent"].queryset = models.Department.objects.filter(
            is_active=True
        ).order_by("sort_order", "title")

        # 编辑时，不能出现自己是自己的上级
        if self.instance.pk:
            self.fields["parent"].queryset = self.fields["parent"].queryset.exclude(
                pk=self.instance.pk
            )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        current = parent

        # 防止把本部门或自己的下级部门设为上级，造成循环层级。
        while current:
            if self.instance.pk and current.pk == self.instance.pk:
                raise ValidationError("不能将本部门或下级部门设为上级部门")
            current = current.parent

        return parent


class PositionModelForm(BootstrapModelForm):
    class Meta:
        model = models.Position
        fields = ["department", "name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].required = True
        self.fields["department"].queryset = models.Department.objects.filter(
            is_active=True
        ).order_by("title")


class UserModelForm(BootstrapModelForm):
    name = forms.CharField(min_length=2, label="姓名")

    class Meta:
        model = models.Employee
        fields = [
            "name",
            "employee_no",
            "age",
            "gender",
            "entry_date",
            "department",
            "position",
        ]
        # 插件添加样式的手动写法（不利用源码）
        widgets={
           "entry_date":forms.DateInput(attrs={"type":"date"})
        }

    # 下面的构造方法配置表单字段对象的属性，可以负责什么样的数据可以有效
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["department"].required = True
        self.fields["position"].required = True
        self.fields["department"].queryset = models.Department.objects.filter(
            is_active=True
        ).order_by("title")
        # department__is_active=True跨关联模型查询，默认条件为exact
        # Q,组合查询条件
        position_filter = Q(is_active=True, department__is_active=True)

        # 编辑员工时，保留当前职位选项，即使这个职位后来被停用了。self是当前表单实例，self.instance是关联的Employee模型对象
        if self.instance.pk and self.instance.position_id:
            position_filter |= Q(pk=self.instance.position_id)
        self.fields["position"].queryset = (
            models.Position.objects.filter(position_filter)
            .select_related("department")
            .order_by("department__title", "name")
        )

    # 多字段校验一般卸载clean方法中，单字段检验写在clean_字段名方法中。
    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        position = cleaned_data.get("position")
        if department and position and position.department_id != department.pk:
            self.add_error("position", "所选职位不属于所选部门")
        return cleaned_data


class AdminModelForm(BootstrapModelForm):
    confirm_password = forms.CharField(
        label="确认密码", widget=forms.PasswordInput(render_value=True)
    )  # 加入参数render_value=True，能够在密码校验前后不一致情况下不清空密码
    is_active = forms.TypedChoiceField(
        label="是否启用",
        choices=(
            (True, "是"),
            (False, "否"),
        ),
        coerce=lambda value: value == "True",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = models.Account
        fields = ["username", "password", "confirm_password", "is_active"]
        widgets = {"password": forms.PasswordInput}

    # md5加密方式替换为django的hashers中的加密模式
    # 钩子函数的调用执行顺序按照fields中的字段顺序而不是函数上下顺序
    def clean_password(self):
        # return md5(self.cleaned_data.get('password'))
        password = self.cleaned_data.get("password")
        if not password:
            raise ValidationError("密码不能为空")
        return password

    def clean_confirm_password(self):
        # 定义钩子方式校验加密后的 密码和确认密码的值是否一致
        # pwd = self.cleaned_data.get('password')
        # confirm_pwd = md5(self.cleaned_data.get('confirm_password'))
        # if pwd != confirm_pwd:
        #     raise ValidationError('密码不一致')
        # return confirm_pwd
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.password = make_password(self.cleaned_data["password"])
        if commit:
            obj.save()
        return obj


class AdminRoleForm(forms.ModelForm):

    groups = forms.ModelMultipleChoiceField(
        label="角色", queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = models.Account
        fields = ["groups"]

    # 控制SuperAdmin至少保留一个
    def clean_groups(self):
        groups = self.cleaned_data.get("groups")
        if groups is None:
            return groups
        is_superadmin = groups.filter(name="SuperAdmin").exists()
        if not is_superadmin:
            other_superadmin_count = (
                models.Account.objects.filter(groups__name="SuperAdmin")
                .exclude(id=self.instance.pk)
                .count()
            )
            if other_superadmin_count == 0:
                raise ValidationError("系统至少需要保留一个SuperAdmin")
        return groups

    # 权限控制接入view层，作为装饰器控制
    # 根据权限动态显示groups字段
    # def __init__(self, *args,can_manage_roles=False, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if not can_manage_roles:
    #         self.fields.pop('groups')


class AdminResetModelForm(BootstrapModelForm):
    confirm_password = forms.CharField(
        label="确认密码", widget=forms.PasswordInput(render_value=True)
    )
    # 加入参数render_value=True，能够在密码校验前后不一致情况下不清空密码
    password = forms.CharField(
        label="新密码", widget=forms.PasswordInput, max_length=128
    )

    class Meta:
        model = models.Account
        fields = ["password", "confirm_password"]

    def clean_password(self):
        # md5_pwd = md5(self.cleaned_data.get('password'))
        # # 根据instance中的id值和新输入密码的md5密文为条件在数据库中搜索，如果存在则表明新密码和旧密码相同，则提示错误
        # exist = models.Admin.objects.filter(id=self.instance.pk, password=md5_pwd).exists()
        # if exist:
        #     raise ValidationError("不能和旧密码一致")
        # return md5_pwd
        password = self.cleaned_data.get("password")
        if not password:
            raise ValidationError("密码不能为空")
        return password

    def clean_confirm_password(self):
        # print(self.cleaned_data)
        # pwd = self.cleaned_data.get('password')
        # confirm_pwd = md5(self.cleaned_data.get('confirm_password'))
        # if pwd != confirm_pwd:
        #     raise ValidationError('密码不一致')
        # return confirm_pwd
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.password = make_password(self.cleaned_data["password"])
        if commit:
            obj.save()
        return obj


class ProjectBusinessForm(BootstrapModelForm):
    """商务人员创建项目并维护客户、合同和负责人信息"""

    class Meta:
        model = models.Project
        fields = [
            "name",
            "customer_name",
            "project_type",
            "contract_amount",
            "manager",
            "planned_start",
            "planned_end",
        ]
        widgets = {
            "planned_start": forms.DateInput(attrs={"type": "date"}),
            "planned_end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manager"].required = False
        self.fields["manager"].queryset = (
            models.Account.objects.filter(
                is_active=True, employee__isnull=False, groups__name="ProjectManager"
            )
            .distinct()
            .order_by("username")
        )


class ProjectDesignForm(BootstrapModelForm):
    """项目负责人维护项目阶段和设计要求"""

    class Meta:
        model = models.Project
        fields = ["stage", "status", "design_requirements"]
        widgets = {
            "design_requirements": forms.Textarea(attrs={"rows": 6}),
        }


class ProjectResourceForm(BootstrapModelForm):
    """共享盘资料表单。用户只录入共享盘键和相对路径，禁止填写绝对路径"""

    class Meta:
        model = models.ProjectResource
        fields = [
            "display_name",
            "category",
            "resource_type",
            "share_root",
            "relative_path",
            "note",
            "is_active",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_relative_path(self):
        raw_path = self.cleaned_data["relative_path"].strip()
        normalized = raw_path.replace("\\", "/")
        # Windows 路径规则解析，能按 Windows 规则识别反斜杠 \、盘符和 UNC 路径
        windows_path = PureWindowsPath(raw_path)
        # POSIX（Linux/macOS）路径规则解析
        posix_path = PurePosixPath(normalized)

        # 仅接收相对于共享盘根目录的路径，拒绝盘符、根路径和目录回退。
        if (
            not normalized
            or windows_path.is_absolute()
            or windows_path.drive
            or posix_path.is_absolute()
            or ".." in posix_path.parts
            or posix_path == PurePosixPath(".")
        ):
            raise ValidationError("请输入安全的共享盘相对路径")
        return posix_path.as_posix()


class ProjectPaymentForm(BootstrapModelForm):
    amount = forms.DecimalField(
        label="到账金额", min_value=0.01, max_digits=14, decimal_places=2
    )

    class Meta:
        model = models.ProjectPayment
        fields = ["source_order", "amount", "received_on", "note"]
        widgets = {
            "received_on": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.fields["source_order"].required = False
        self.fields["source_order"].queryset = models.Order.objects.filter(
            project=project, type=4
        ).order_by("-created_at")

    def clean(self):
        cleaned_data = super().clean()
        source_order = cleaned_data.get("source_order")

        if source_order and source_order.project_id != self.project.pk:
            self.add_error("source_order", "请选择当前项目的收款/开票工单")
        return cleaned_data


class TaskAssignmentForm(BootstrapModelForm):
    """项目负责人使用：维护任务内容和分配对象"""

    class Meta:
        model = models.TaskManage
        fields = [
            "project",
            "source_order",
            "level",
            "title",
            "detail",
            "executor",
            "due_date",
        ]
        widgets = {
            "detail": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

        labels = {
            "level": "优先级",
            "title": "任务名称",
            "detail": "任务说明",
            "executor": "执行员工",
            "due_date": "截止日期",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["project"].required = False
        self.fields["project"].queryset = models.Project.objects.exclude(
            status__in=["completed", "terminated"]
        ).order_by("project_code")

        self.fields["source_order"].required = False
        self.fields["source_order"].queryset = models.Order.objects.exclude(
            status__in=[
                models.Order.STATUS_COMPLETED,
                models.Order.STATUS_REJECTED,
                models.Order.STATUS_CANCELLED,
            ]
        ).order_by("-created_at")

        # 只允许把任务分配给有启用登录账号的员工。
        self.fields["executor"].queryset = (
            models.Employee.objects.filter(login_account__is_active=True)
            .select_related("department")
            .order_by("name")
        )

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        source_order = cleaned_data.get("source_order")

        if source_order and source_order.project_id != (
            project.pk if project else None
        ):
            self.add_error(
                "source_order",
                "任务项目必须和来源工单所属项目一致",
            )
        return cleaned_data


class TaskProgressForm(BootstrapModelForm):
    """员工使用：不能从表单修改任务标题、执行人等字段。"""

    # ChoiceField 是一个用于处理“下拉选择框”（Select）或单选列表的字段。
    # 限制用户只能从预先定义好的选项列表中选择一个值，如果用户提交了不在列表中的选项，表单验证就会报错。
    status = forms.ChoiceField(
        label="任务状态",
        choices=(
            (models.TaskManage.STATUS_IN_PROGRESS, "进行中"),
            (models.TaskManage.STATUS_BLOCKED, "受阻"),
            (models.TaskManage.STATUS_COMPLETED, "已完成"),
        ),
    )

    progress = forms.IntegerField(label="完成进度(%)", min_value=0, max_value=100)

    class Meta:
        model = models.TaskProgressLog
        fields = ["status", "progress", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "note": "进度说明",
        }

    def clean(self):
        cleaned_data = super().clean()

        # 标记完成时，进度必须达到 100%。
        if (
            cleaned_data.get("status") == models.TaskManage.STATUS_COMPLETED
            and cleaned_data.get("progress") != 100
        ):
            self.add_error("progress", "状态为已完成时，进度必须是 100%。")

        return cleaned_data


class TaskCancelForm(BootstrapForm):
    """项目负责人取消任务时原因说明"""

    reason = forms.CharField(
        label="撤销说明",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class OrderForm(BootstrapModelForm):
    """商务人员编辑工单资料和指派对象"""

    price = forms.DecimalField(
        label="事项金额",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = models.Order
        fields = [
            "project",
            "title",
            "type",
            "price",
            "expected_payment_date",
            "assignee",
            "detail",
        ]
        widgets = {
            "expected_payment_date": forms.DateInput(attrs={"type": "date"}),
            "detail": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, received_total=Decimal("0.00"),**kwargs):
        super().__init__(*args, **kwargs)
        self.received_total = received_total
        # 负责人必须是启用账号，且关联员工，并属于商务或项目负责人角色。
        self.fields["assignee"].required = True
        self.fields["assignee"].queryset = (
            models.Account.objects.filter(
                is_active=True,
                employee__isnull=False,
                groups__name__in=["BusinessAdmin", "ProjectManager"],
            )
            .distinct()
            .order_by("username")
        )
        # 项目如果存在要排除已完成和已终止的状态的
        self.fields["project"].required = False
        self.fields["project"].queryset = models.Project.objects.exclude(
            status__in=["completed", "terminated"]
        ).order_by("project_code")

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        if (
            price is not None
            and self.received_total is not None
            and self.received_total > price
        ):
            self.add_error(
                "received_total",
                "累计回款不可超过事项金额",
            )
        return cleaned_data


class OrderProgressForm(BootstrapModelForm):
    """工单负责人更新处理状态并留下说明"""

    status = forms.TypedChoiceField(
        label="处理状态",
        choices=models.Order.STATUS_CHOICES,
        coerce=int,
    )

    class Meta:
        model = models.OrderProgressLog
        fields = ["status", "note"]
        # 前端渲染控件
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {"note": "处理说明"}


class LoginForm(BootstrapForm):
    username = forms.CharField(
        label="用户名", widget=forms.TextInput(attrs={"autocomplete": "off"})
    )
    password = forms.CharField(
        label="密码", widget=forms.PasswordInput(render_value=True), required=True
    )
    code = forms.CharField(
        label="验证码",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        required=True,
    )

    # 取消旧的md5的密码加密模式，后续渐进改成django支持的新的加密模式譬如PBKDF2等
    # def clean_password(self):
    #     pwd = md5(self.cleaned_data["password"])
    #     return pwd


# 当前登录账号修改自己密码
class AccountChangePasswordForm(BootstrapForm):
    old_password = forms.CharField(
        label="旧密码",
        widget=forms.PasswordInput,
    )
    new_password = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True),
    )

    def __init__(self, *args, current_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_account = current_account

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")

        if not self.current_account:
            raise ValidationError("账号不存在")

        if not check_password(old_password, self.current_account.password):
            raise ValidationError("旧密码错误")

        return old_password

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get("new_password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise ValidationError("两次密码不一致")

        return confirm_password


class ProfileInfoForm(BootstrapModelForm):
    class Meta:
        model = models.ProfileInfo
        fields = ["nickname", "signature"]


class AccountModelForm(BootstrapModelForm):
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True),
    )
    password = forms.CharField(
        label="密码",
        max_length=128,
        widget=forms.PasswordInput(),
    )
    is_active = forms.TypedChoiceField(
        label="是否启用",
        choices=((True, "是"), (False, "否")),
        coerce=lambda value: value == "True",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = models.Account
        fields = ["username", "password", "confirm_password", "is_active"]

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password:
            raise ValidationError("密码不能为空")
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm_password = cleaned.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "密码不一致")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.password = make_password(self.cleaned_data["password"])
        if commit:
            obj.save()
        return obj


class AccountResetModelForm(BootstrapModelForm):
    password = forms.CharField(
        label="新密码",
        max_length=128,
        widget=forms.PasswordInput(),
    )
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(render_value=True),
    )

    class Meta:
        model = models.Account
        fields = ["password", "confirm_password"]

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm_password = cleaned.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "密码不一致")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.password = make_password(self.cleaned_data["password"])
        if commit:
            obj.save(update_fields=["password", "updated_at"])
        return obj


class AccountRoleForm(forms.ModelForm):

    # ModelMultipleChoiceField专门用来处理 “多对多（ManyToManyField）” 或 “外键（ForeignKey，反向多选）” 关系的表单字段。
    # 配合不同的 Widget（小部件） 来改变它的外观：
    # 复选框组（CheckboxSelectMultiple）：最常见，渲染成一排并排的复选框，方便用户直接勾选多个。
    groups = forms.ModelMultipleChoiceField(
        label="角色",
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = models.Account
        fields = ["groups"]

    def clean_groups(self):
        groups = self.cleaned_data.get("groups")
        if groups is None or groups.filter(name="SuperAdmin").exists():
            return groups

        other_superadmin_count = (
            models.Account.objects.filter(groups__name="SuperAdmin")
            .exclude(pk=self.instance.pk)
            .distinct()
            .count()
        )

        if other_superadmin_count == 0:
            raise ValidationError("系统至少需要保留一个 SuperAdmin")
        return groups

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = Group.objects.exclude(name="RegularEmployee")

    def save(self, commit=True):
        account = super().save(commit)
        if account.employee_id:
            regular_employee_group = Group.objects.get(name="RegularEmployee")
            account.groups.add(regular_employee_group)
        return account


class AvatarUploadForm(BootstrapForm):
    avatar = forms.ImageField(label="头像")


class EmployeeCreateForm(UserModelForm):
    account_username = forms.CharField(
        label="登录用户名",
        max_length=32,
    )
    initial_password = forms.CharField(
        label="初始密码",
        widget=forms.PasswordInput,
        strip=False,
    )
    confirm_password = forms.CharField(
        label="确认初始密码", widget=forms.PasswordInput, strip=False
    )

    def clean_account_username(self):
        username = self.cleaned_data["account_username"].strip()
        if models.Account.objects.filter(username__iexact=username).exists():
            raise ValidationError("登录用户名已存在")
        return username

    # 跨字段校验
    def clean(self):
        # 显示调用父类clean方法的原因是，可以启用后续模型唯一性校验
        # 实际super().clean()就是self.cleaned_data
        cleaned_data = super().clean()
        password = cleaned_data.get("initial_password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "两次输入密码不一致")
        return cleaned_data
