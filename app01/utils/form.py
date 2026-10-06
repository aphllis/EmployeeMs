from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password,make_password
from django.contrib.auth.models import Group

from app01 import models
from app01.utils.bootstrap import BootstrapModelForm,BootstrapForm
# 引入正则校验
class DepartModelForm(BootstrapModelForm):
    title = forms.CharField(label='部门名')

    class Meta:
        model = models.Department
        fields = ['title']


class UserModelForm(BootstrapModelForm):
    name = forms.CharField(min_length=2, label='用户名')

    class Meta:
        model = models.Employee
        fields = ['name', 'age', 'gender', 'password', 'account', 'entrytime', 'depart']
        # 插件添加样式的手动写法（不利用源码）
        # widgets={
        #     'name':forms.TextInput(attrs={'class':'form-control mb-3'}),
        #     'password':forms.PasswordInput(attrs={'class':'form-control mb-3'})
        # }


# 利用源码循环添加样式功能已封装入BootstrapModelForm中
# def __init__(self, *args, **kwargs):
#     super().__init__(*args, **kwargs)
#     for name, fld in self.fields.items():
#         if fld.widget.attrs:
#             fld.widget.attrs['class']='form-control mb-3'
#             fld.widget.attrs['PlaceHolder']=fld.label
#         else:
#             fld.widget.attrs = {'class': 'form-control mb-3', 'PlaceHolder': fld.label}

class TelModelForm(BootstrapModelForm):
    # 验证方式一：
    # 给手机号添加正则校验
    mobile = forms.CharField(
        label='手机号',
        validators=[RegexValidator(r'^1\d{10}$', '手机号格式错误')]
    )

    class Meta:
        model = models.Telenumber
        fields = ['mobile', 'price', 'level', 'status']
        # fields='__all__' 代表所有字段
        # exclude=['field_1'] 代表排除某个字段

    # 验证方式二(钩子方法)：
    # cleaned_data是一个字典，保存所有了类实例的表单键值，在视图函数中执行form.save()时，如果有钩子方法会调用它，然后将返回值更新到对应键，然后保存到数据库
    # 定义clean_field_name函数，是定义钩子方法，最后要返回对应键的值
    def clean_mobile(self):
        txt_mobile = self.cleaned_data['mobile']
        # 针对添加时，手机号重复问题的校验有两个方式
        # 方式一:直接在models里面在创建表结构类时，在mobile字段定义里面添加参数unique=True
        # 方式二:在views视图函数中，创建ModelForm类时在钩子方法中通过查询对应mobile判断是否存在，已存在则抛出对应错误
        # exists=models.Telenumber.objects.filter(mobile=txt_mobile).exists()
        # if exists:
        #     raise ValidationError('手机号已存在')
        # 如果校验不通过，抛出错误信息
        if len(txt_mobile) != 11:
            raise ValidationError('格式错误')
        # 否则直接返回值
        return txt_mobile
        # 方式二的注意点在于，对于编辑手机号方法而言，不能直接这样使用，否则如果要修改其他而保留手机号时会报手机号已存在错误
        # 解决方式二对于编辑手机方法存在的问题，可以通过排除自己以外判断是否存在重复的号码，代码为：(self.instance.pk 就是行对象的id值)
        # exists=models.Telenumber.objects.exclude(id=self.instance.pk).filter(mobile=txt_mobile).exists()


class AdminModelForm(BootstrapModelForm):
    confirm_password = forms.CharField(label='确认密码',
                                       widget=forms.PasswordInput(
                                           render_value=True))  # 加入参数render_value=True，能够在密码校验前后不一致情况下不清空密码
    is_active=forms.TypedChoiceField(
        label='是否启用',
        choices=(
            (True,'是'),
            (False,'否'),
        ),
        coerce=lambda value:value == 'True',
        widget=forms.RadioSelect
    )
    class Meta:
        model = models.Admin
        fields = ['username', 'password', 'confirm_password','is_active']
        widgets = {
            'password': forms.PasswordInput
        }
    # md5加密方式替换为django的hashers中的加密模式
    # 钩子函数的调用执行顺序按照fields中的字段顺序而不是函数上下顺序
    def clean_password(self):
        # return md5(self.cleaned_data.get('password'))
        password=self.cleaned_data.get('password')
        if not password:
            raise ValidationError('密码不能为空')
        return password

    
    def clean_confirm_password(self):
        # 定义钩子方式校验加密后的 密码和确认密码的值是否一致
        # pwd = self.cleaned_data.get('password')
        # confirm_pwd = md5(self.cleaned_data.get('confirm_password'))
        # if pwd != confirm_pwd:
        #     raise ValidationError('密码不一致')
        # return confirm_pwd
        password=self.cleaned_data.get('password')
        confirm_password=self.cleaned_data.get('confirm_password')
        if password!=confirm_password:
            raise ValidationError('密码不一致')
        return confirm_password

    def save(self,commit=True):
        obj=super().save(commit=False)
        obj.password=make_password(
            self.cleaned_data['password']
        )
        if commit:
            obj.save()
        return obj


class AdminRoleForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        label='角色',
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    class Meta:
        model=models.Admin
        fields=['groups']
    # 控制SuperAdmin至少保留一个
    def clean_groups(self):
        groups=self.cleaned_data.get('groups')
        if groups is None:
            return groups
        is_superadmin=groups.filter(name='SuperAdmin').exists()
        if not is_superadmin:
            other_superadmin_count=models.Admin.objects.filter(
                groups__name='SuperAdmin'
            ).exclude(
                id=self.instance.pk
            ).count()
            if other_superadmin_count==0:
                raise ValidationError(
                    '系统至少需要保留一个SuperAdmin'
                )
        return groups
    # 权限控制接入view层，作为装饰器控制
    # 根据权限动态显示groups字段
    # def __init__(self, *args,can_manage_roles=False, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if not can_manage_roles:
    #         self.fields.pop('groups')




class AdminResetModelForm(BootstrapModelForm):
    confirm_password = forms.CharField(label='确认密码',
                                       widget=forms.PasswordInput(
                                           render_value=True))
    # 加入参数render_value=True，能够在密码校验前后不一致情况下不清空密码
    password = forms.CharField(label='新密码', widget=forms.PasswordInput, max_length=128)

    class Meta:
        model = models.Admin
        fields = ['password', 'confirm_password']

    def clean_password(self):
        # md5_pwd = md5(self.cleaned_data.get('password'))
        # # 根据instance中的id值和新输入密码的md5密文为条件在数据库中搜索，如果存在则表明新密码和旧密码相同，则提示错误
        # exist = models.Admin.objects.filter(id=self.instance.pk, password=md5_pwd).exists()
        # if exist:
        #     raise ValidationError("不能和旧密码一致")
        # return md5_pwd
        password=self.cleaned_data.get('password')
        if not password:
            raise ValidationError('密码不能为空')
        return password

    def clean_confirm_password(self):
        # print(self.cleaned_data)
        # pwd = self.cleaned_data.get('password')
        # confirm_pwd = md5(self.cleaned_data.get('confirm_password'))
        # if pwd != confirm_pwd:
        #     raise ValidationError('密码不一致')
        # return confirm_pwd
        password=self.cleaned_data.get('password')
        confirm_password=self.cleaned_data.get('confirm_password')
        if password!=confirm_password:
            raise ValidationError('密码不一致')
        return confirm_password
    def save(self, commit = True):
        obj=super().save(commit=False)
        obj.password=make_password(self.cleaned_data['password'])
        if commit:
            obj.save()
        return obj



class TaskModelForm(BootstrapModelForm):
    class Meta:
        model = models.TaskManage
        fields = "__all__"
        widgets={
            'detail':forms.TextInput,
        }


class LoginForm(BootstrapForm):
    username = forms.CharField(label="用户名", widget=forms.TextInput(attrs={"autocomplete": "off"}))
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

#当前管理员账号修改自己密码
class AdminChangePasswordForm(forms.Form):
    old_password=forms.CharField(label="旧密码",widget=forms.PasswordInput)

    new_password=forms.CharField(label="新密码",widget=forms.PasswordInput)

    confirm_password=forms.CharField(label="确认密码",widget=forms.PasswordInput(render_value=True))

    def __init__(self,*args,current_admin=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.current_admin=current_admin

    def clean_old_password(self):
        old_password=self.clean_old_password.get("old_password")

        if not self.current_admin:
            raise ValidationError("账号不存在")

        if not check_password(old_password,self.current_admin.password):
            raise ValidationError("旧密码错误")

        return old_password

    def clean_confirm_password(self):
        new_password=self.cleaned_data.get("new_password")
        confirm_password=self.cleaned_data.get("confirm_password")

        if new_password !=confirm_password:
            raise ValidationError("两次密码不一致")
        return confirm_password
    
