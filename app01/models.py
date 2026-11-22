from pathlib import PureWindowsPath

from django.db import models
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from django.contrib.auth.models import Group
from django.contrib.auth import get_backends


# Create your models here.
class Admin(models.Model):
    """管理员表"""

    username = models.CharField(verbose_name="用户名", max_length=32, unique=True)
    # 旧的md5升级到新密码模式，密码最大长度从64升级到128
    password = models.CharField(verbose_name="密码", max_length=128)

    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    groups = models.ManyToManyField(
        Group, blank=True, related_name="custom_admins", verbose_name="角色组"
    )

    class Meta:
        permissions = [
            ("manage_admin_roles", "can manage admin roles"),
            ("reset_admin_password", "can reset admin password"),
        ]

    def has_perm(self, perm, obj=None):
        """判断当前管理员是否拥有指定权限"""
        for backend in get_backends():
            if backend.has_perm(self, perm, obj):
                return True
        return False

    def __str__(self):
        return self.username


class Department(models.Model):
    """部门表"""

    title = models.CharField(verbose_name="部门名", max_length=32)

    code = models.CharField(verbose_name="部门编码", max_length=16, unique=True)

    parent = models.ForeignKey(
        "self",
        verbose_name="上级部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    description = models.TextField(verbose_name="部门说明", blank=True)
    sort_order = models.PositiveIntegerField(
        verbose_name="显示顺序",
        default=0,
    )
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class Position(models.Model):
    """职位表"""

    department = models.ForeignKey(
        "Department",
        verbose_name="所属部门",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="positions",
    )
    name = models.CharField(verbose_name="职位名称", max_length=64)

    description = models.CharField(verbose_name="说明", max_length=255, blank=True)
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    # Meta模型配置类，配置整个模型
    class Meta:
        # 约束列表
        constraints = [
            # 唯一约束
            models.UniqueConstraint(
                # 唯一性由两个字段组合决定，一个是外键一个是模型自己的字段
                fields=["department", "name"],
                # 约束名
                name="uniq_position_name_per_department",
            )
        ]

    def __str__(self):
        if self.department_id:
            return f"{self.department.title}-{self.name}"
        return self.name


class Employee(models.Model):
    """员工表"""

    name = models.CharField(verbose_name="姓名", max_length=32)
    employee_no = models.CharField(
        verbose_name="工号", max_length=32, unique=True, null=True, blank=True
    )
    age = models.IntegerField(verbose_name="年龄", null=True, blank=True)
    gender_choices = ((1, "男"), (2, "女"))
    gender = models.SmallIntegerField(
        verbose_name="性别", choices=gender_choices, null=True, blank=True
    )
    entry_date = models.DateField(verbose_name="入职时间", null=True, blank=True)

    # 无约束，部门id
    # department_id=models.BigIntegerField(verbose_name='部门id')

    # 有约束
    # django 会将外键department改成department_id
    # on_delete=models.CASCADE,级联的删除
    department = models.ForeignKey(
        "Department",
        verbose_name="所属部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    # 置空的删除，确保该字段能够为空null=True,blank=True
    # department=models.ForeignKey(to="Department",to_field="id",null=True,blank=True,on_delete=SET_NULL)
    position = models.ForeignKey(
        "Position",
        verbose_name="职位",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    # django的约束


class Project(models.Model):
    """项目台账，保存项目相关信息、阶段和设计要求"""
    TYPE_CHOICES = (
        ("architecture", "建筑设计"),
        ("interior", "室内设计"),
        ("landscape", "景观设计"),
        ("planning", "规划设计"),
        ("other", "其他"),
    )
    # 阶段 描述项目工作处于哪个设计环节
    STAGE_CHOICES = (
        ("opportunity", "项目跟进"),
        ("concept", "方案设计"),
        ("schematic", "初步设计"),
        ("construction", "施工图设计"),
        ("site_service", "施工配合"),
        ("closeout", "竣工归档"),
    )
    # 状态 描述项目是否仍在进行
    STATUS_CHOICES = (
        ("active", "进行中"),
        ("paused", "暂停"),
        ("completed", "已完成"),
        ("terminated", "已终止"),
    )
    project_code = models.CharField(verbose_name="项目编号", max_length=32, unique=True)
    name = models.CharField(verbose_name="项目名称", max_length=128)
    customer_name = models.CharField(verbose_name="客户名称", max_length=128)
    project_type = models.CharField(
        verbose_name="项目类型",
        max_length=32,
        choices=TYPE_CHOICES,
    )
    stage = models.CharField(
        verbose_name="项目阶段",
        max_length=32,
        choices=STAGE_CHOICES,
        default="opportunity",
    )
    status = models.CharField(
        verbose_name="项目状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default="active",
    )
    # 保存当前版本的设计要求
    design_requirements = models.TextField(verbose_name="设计要求", blank=True)
    contract_amount = models.DecimalField(
        verbose_name="合同金额",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        # 如果字段值为负数会触发validationError
        # 该校验是表单层面验证，而save()或obj.create()不会自动执行
        validators=[MinValueValidator(Decimal("0"))],
    )
    # Account 账号中包含了角色权限，项目负责人使用账号外键
    # 项目初期跟进阶段，负责人允许为空
    manager = models.ForeignKey(
        "Account",
        verbose_name="项目负责人",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="managed_projects",
    )
    planned_start = models.DateField(verbose_name="计划开始时间", null=True, blank=True)
    planned_end = models.DateField(verbose_name="计划结束时间", null=True, blank=True)
    created_by = models.ForeignKey(
        "Account",
        verbose_name="创建账号",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at", "-id"]
        # 本质权限的申明，在执行数据库迁移后才会将权限创建写入权限库
        permissions = [
            (
                "view_assigned_project",
                "Can view projects with tasks assigned to the current employee",
            ),
            (
                "change_project_design",
                "Can change design stage and requirements of projects",
            ),
        ]
        # 添加数据库层面和合同金额非负校验
        constraints = [
            models.CheckConstraint(
                condition=models.Q(contract_amount__gte=Decimal("0")),
                name="project_contract_amount_nonnegative",
            ),
        ]
    def clean(self):
        # 无论从表单还是绕过表单都要判断计划日期
        # form中的clean主要用于处理与表单提交时相关的逻辑校验
        # model中的clean主要用与数据硬性校验规则
        if (
            self.planned_start
            and self.planned_end
            and self.planned_end < self.planned_start
        ):
            raise ValidationError({"planned_end": "计划结束日期不能早于计划开始日期"})
    def __str__(self):
        return f"{self.project_code} - {self.name}"

class ProjectResource(models.Model):
    """共享盘资料索引；只保存位置和说明，不上传任何文件"""

    CATEGORY_CHOICES = (
        ("brief", "项目输入"),
        ("contract", "合同资料"),
        ("reference", "参考资料"),
        ("drawing", "图纸目录"),
        ("model", "模型目录"),
        ("text", "文本目录"),
        ("issued", "正式交付"),
        ("other", "其他"),
    )

    RESOURCE_TYPE_CHOICES = (("folder", "文件夹"), ("file", "文件"))

    SHARE_ROOT_CHOICES = (
        ("design", "设计共享盘"),
        ("business", "商务共享盘"),
        ("archive", "归档共享盘"),
    )

    project = models.ForeignKey(
        Project,
        verbose_name="所属项目",
        on_delete=models.PROTECT,
        related_name="resources",
    )
    display_name = models.CharField(verbose_name="资料名称", max_length=128)
    category = models.CharField(
        verbose_name="资料类别",
        max_length=24,
        choices=CATEGORY_CHOICES,
        default="other",
    )
    resource_type = models.CharField(
        verbose_name="资源类型",
        max_length=12,
        choices=RESOURCE_TYPE_CHOICES,
        default="folder",
    )

    share_root = models.CharField(
        verbose_name="共享盘",
        max_length=24,
        choices=SHARE_ROOT_CHOICES,
    )
    relative_path = models.CharField(verbose_name="相对路径", max_length=500)
    note = models.CharField(verbose_name="说明", max_length=255, blank=True)
    is_active = models.BooleanField(verbose_name="启用", default=True)

    created_by = models.ForeignKey(
        "Account",
        verbose_name="登记账号",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_project_resources",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "display_name", "id"]

    # 让它可以像属性一样读取，不用加括号：`resource.display_path`，而不是 resource.display_path()
    @property
    def display_path(self):
        """用部署配置把共享盘键和相对路径组合为员工可复制的路径"""
        root = settings.PROJECT_SHARE_ROOT.get(self.share_root, "")
        parts = self.relative_path.replace("\\", "/").split("/")

        # 如果配置中找不到root，则生成一个可识别的相对位置返回
        if not root:
            return f"{self.share_root}:/{self.relative_path}"

        path = PureWindowsPath(root)
        for part in parts:
            if part:
                path /= part
        return str(path)

    def __str__(self):
        return f"{self.project.project_code} - {self.display_name}"


class TaskManage(models.Model):
    """任务管理表"""

    level_choices = ((1, "紧急"), (2, "重要"), (3, "临时"))

    # 状态定义
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_BLOCKED = "blocked"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_PENDING, "待开始"),
        (STATUS_IN_PROGRESS, "进行中"),
        (STATUS_BLOCKED, "受阻"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_CANCELLED, "已取消"),
    )
    level = models.SmallIntegerField(
        verbose_name="级别", choices=level_choices, default=1
    )
    title = models.CharField(verbose_name="任务名", max_length=64)

    # 项目任务属于项目，任务允许没有项目
    project = models.ForeignKey(
        Project,
        verbose_name="所属项目",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tasks",
    )

    # 任务可选关联产生它的商务工单
    source_order = models.ForeignKey(
        "Order",
        verbose_name="来源工单",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="spawned_tasks",
    )

    detail = models.TextField(verbose_name="详细信息")

    executor = models.ForeignKey(
        "Employee", on_delete=models.PROTECT, verbose_name="执行者"
    )

    status = models.CharField(
        verbose_name="任务状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    progress = models.PositiveSmallIntegerField(
        verbose_name="完成进度",
        default=0,
    )

    due_date = models.DateField(
        verbose_name="截止日期",
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        "Account",
        verbose_name="创建账号",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
    # auto_now_add 在创建时触发；auto_now在创建或更新时触发
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.source_order_id:
            order_project_id = self.source_order.project_id
            if order_project_id != self.project_id:
                raise ValidationError(
                    {"source_order": "任务项目必须与来源工单项目一致"}
                )

    class Meta:
        permissions = [
            ("view_own_taskmanage", "Can view tasks assigned to the current employee"),
            (
                "update_own_taskmanage",
                "Can submit progress for tasks assigned to the current employee",
            ),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title


class TaskProgressLog(models.Model):
    """任务进度日志，不覆盖之前的说明"""

    task = models.ForeignKey(
        "TaskManage",
        verbose_name="任务进度日志",
        on_delete=models.PROTECT,
        related_name="progress_logs",
    )

    account = models.ForeignKey(
        "Account",
        verbose_name="提交账号",
        on_delete=models.PROTECT,
        related_name="task_progress_logs",
    )
    status = models.CharField(
        verbose_name="提交后的状态",
        max_length=16,
        choices=TaskManage.STATUS_CHOICES,
    )
    # PositiveSmallIntegerField 是一个专门用来存储非负小整数的模型字段（Model Field）
    progress = models.PositiveSmallIntegerField(verbose_name="提交后的进度")
    note = models.TextField(verbose_name="进度说明")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.task.title} - {self.account.username}"


class Order(models.Model):
    """项目商务工单,金额记录事项金额及累计已回款金额"""

    TYPE_CHOICES = (
        (1, "项目报价"),
        (2, "合同变更"),
        (3, "设计变更"),
        (4, "收款/开票"),
        (5, "其他商务事项"),
    )

    STATUS_PENDING = 1
    STATUS_PROCESSING = 2
    STATUS_COMPLETED = 3
    STATUS_REJECTED = 4
    STATUS_CANCELLED = 5

    STATUS_CHOICES = (
        (STATUS_PENDING, "待处理"),
        (STATUS_PROCESSING, "处理中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_REJECTED, "已驳回"),
        (STATUS_CANCELLED, "已取消"),
    )
    oid = models.CharField(verbose_name="工单号", max_length=64, unique=True)
    title = models.CharField(verbose_name="事项名称", max_length=64)
    type = models.SmallIntegerField(
        verbose_name="事项类型",
        choices=TYPE_CHOICES,
        default=5,
    )
    status = models.SmallIntegerField(
        verbose_name="处理状态", choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    # 事项或合同金额；received_amount 是该事项累计已回款金额。
    price = models.DecimalField(
        verbose_name="金额", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    expected_payment_date = models.DateField(
        verbose_name="预计回款日期", null=True, blank=True
    )

    # 工单负责人统一使用 Account
    assignee = models.ForeignKey(
        "Account",
        verbose_name="负责人",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_orders",
    )
    created_by = models.ForeignKey(
        "Account",
        verbose_name="创建账号",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_orders",
    )
    project = models.ForeignKey(
        Project,
        verbose_name="所属项目",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )

    detail = models.TextField(verbose_name="详细说明", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        project_required_type = {1, 2, 3, 4}
        if self.type in project_required_type and not self.project_id:
            raise ValidationError(
                {"project": "报价、合同变更、设计变更和收款事项必须关联项目"}
            )

    class Meta:
        ordering = ["-created_at", "-id"]
        permissions = [
            (
                "update_assigned_order",
                "Can update the status of orders assigned to the current account",
            )
        ]

    def __str__(self):
        return f"{self.oid} - {self.title}"


class OrderProgressLog(models.Model):
    """工单状态变更记录；新增一条记录，不覆盖以前的处理说明"""

    order = models.ForeignKey(
        Order,
        verbose_name="工单",
        on_delete=models.PROTECT,
        related_name="progress_logs",
    )

    account = models.ForeignKey(
        "Account",
        verbose_name="操作账号",
        on_delete=models.PROTECT,
        related_name="progress_logs",
    )
    status = models.SmallIntegerField(
        verbose_name="变更后状态",
        choices=Order.STATUS_CHOICES,
    )
    note = models.TextField(verbose_name="处理说明")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.order.oid} - {self.account.username}"


class ProjectPayment(models.Model):
    """实际到账记录；累计回款由这些记录汇总，不从工单金额推算"""

    project = models.ForeignKey(
        Project,
        verbose_name="项目",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    source_order = models.ForeignKey(
        Order,
        verbose_name="关联收款/开票工单",
        on_delete=models.PROTECT,
        # null=True:表示数据库允许该字段储存sql NULL
        null=True,
        # blank=True,表示表单和模型验证允许该字段留空
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(
        verbose_name="到账金额",
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    received_on = models.DateField(verbose_name="到账日期")
    note = models.TextField(verbose_name="说明", blank=True)
    recorded_by = models.ForeignKey(
        "Account",
        verbose_name="登记账号",
        on_delete=models.PROTECT,
        related_name="recorded_project_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_on", "-id"]

    def clean(self):
        if self.source_order_id:
            if self.source_order.project_id != self.project_id:
                raise ValidationError({"source_order": "收款工单必须属于当前项目"})
            if self.source_order.type != 4:
                raise ValidationError({"source_order": "只能关联“收款/开票”类型工单"})

    def __str__(self):
        return f"{self.project.project_code} - {self.amount}"


class ProfileInfo(models.Model):
    admin = models.OneToOneField(
        "Admin",
        on_delete=models.CASCADE,
        related_name="profile_info",
        verbose_name="管理员",
        null=True,
        blank=True,
    )
    account = models.OneToOneField(
        "Account",
        on_delete=models.CASCADE,
        related_name="profile_info",
        verbose_name="登录账号",
        null=True,
        blank=True,
    )
    nickname = models.CharField(verbose_name="昵称", max_length=32, unique=True)
    signature = models.CharField(verbose_name="个性签名", max_length=128, blank=True)

    # 多对一外键
    department = models.ForeignKey(
        "Department",
        on_delete=models.SET_NULL,
        # 数据库层面允许为空
        null=True,
        # 表单验证层面允许为空
        blank=True,
        # 反向关系访问
        related_name="profiles",
        verbose_name="所属部门",
    )
    position = models.CharField(verbose_name="职位", max_length=32, blank=True)
    # avatar = models.CharField(verbose_name="头像", max_length=128, blank=True)
    avatar = models.ImageField(
        verbose_name="头像", upload_to="avatars/", max_length=255, blank=True
    )

    age = models.IntegerField(verbose_name="年龄", null=True, blank=True)
    gender_choices = ((1, "男"), (2, "女"))
    gender = models.SmallIntegerField(
        verbose_name="性别", choices=gender_choices, null=True, blank=True
    )
    email = models.CharField(verbose_name="邮箱", max_length=64, null=True, blank=True)


class Account(models.Model):
    """系统登录账号"""

    username = models.CharField(verbose_name="用户名", max_length=32, unique=True)

    password = models.CharField(verbose_name="密码", max_length=128)

    email = models.EmailField(
        verbose_name="邮箱", max_length=254, unique=True, null=True, blank=True
    )

    email_verified = models.BooleanField(verbose_name="邮箱已验证", default=False)

    phone = models.CharField(
        verbose_name="手机号", max_length=20, unique=True, null=True, blank=True
    )

    phone_verified = models.BooleanField(verbose_name="手机已验证", default=False)

    groups = models.ManyToManyField(
        Group, blank=True, related_name="accounts", verbose_name="角色组"
    )

    employee = models.OneToOneField(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_account",
        verbose_name="关联员工",
    )

    is_active = models.BooleanField(verbose_name="是否启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("manage_account_roles", "can manage account roles"),
            ("reset_account_password", "can reset account password"),
        ]

    def has_perm(self, perm, obj=None):
        """判断当前账号是否拥有指定权限"""
        for backend in get_backends():
            if backend.has_perm(self, perm, obj):
                return True
        return False

    def __str__(self):
        return self.username
