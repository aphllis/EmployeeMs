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

        self.fields["parent"].queryset=models.Department.objects.filter(
            is_active=True
        ).order_by("sort_order","title")

        # 编辑时，不能出现自己是自己的上级
        if self.instance.pk:
            self.fields["parent"].queryset=self.fields["parent"].queryset.exclude(pk=self.instance.pk)
     
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
        model=models.Position
        fields=["department","name","description"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].required=True
        self.fields["department"].queryset=models.Department.objects.filter(is_active=True).order_by("title")




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
        # widgets={
        #     'name':forms.TextInput(attrs={'class':'form-control mb-3'}),
        #     'password':forms.PasswordInput(attrs={'class':'form-control mb-3'})
        # }

    # 下面的构造方法配置表单字段对象的属性，可以负责什么样的数据可以有效
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["department"].required=True
        self.fields["position"].required=True
        self.fields["department"].queryset=models.Department.objects.filter(
            is_active=True
        ).order_by("title")
        #department__is_active=True跨关联模型查询，默认条件为exact
        # Q,组合查询条件
        position_filter=Q(is_active=True,department__is_active=True)

        # 编辑员工时，保留当前职位选项，即使这个职位后来被停用了。self是当前表单实例，self.instance是关联的Employee模型对象
        if self.instance.pk and self.instance.position_id:
            position_filter|=Q(pk=self.instance.position_id)
        self.fields["position"].queryset=(
            models.Position.objects.filter(position_filter)
            .select_related("department")
            .order_by("department__title","name")
        )
    # 多字段校验一般卸载clean方法中，单字段检验写在clean_字段名方法中。
    def clean(self):
        cleaned_data=super().clean()
        department=cleaned_data.get("department")
        position=cleaned_data.get("position")
        if (
            department and position and position.department_id !=department.pk
        ):
            self.add_error("position","所选职位不属于所选部门")
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


class TaskModelForm(BootstrapModelForm):
    class Meta:
        model = models.TaskManage
        fields = "__all__"
        widgets = {
            "detail": forms.TextInput,
        }


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
            regular_employee_group=Group.objects.get(name="RegularEmployee")
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
        #显示调用父类clean方法的原因是，可以启用后续模型唯一性校验
        #实际super().clean()就是self.cleaned_data
        cleaned_data = super().clean()
        password = cleaned_data.get("initial_password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "两次输入密码不一致")
        return cleaned_data
