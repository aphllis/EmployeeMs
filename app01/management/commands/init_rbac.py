from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app01 import models


class Command(BaseCommand):
    help = "Initialize RBAC roles and permissions"

    def handle(self, *args, **options):
        # 1.创建角色(此处即权限组Group)
        superadmin, _ = Group.objects.get_or_create(name="SuperAdmin")
        hr_admin, _ = Group.objects.get_or_create(name="HRAdmin")
        business_admin, _ = Group.objects.get_or_create(name="BusinessAdmin")
        readonly, _ = Group.objects.get_or_create(name="ReadOnly")
        # if created:
        #     self.stdout.write(self.style.SUCCESS("Created group: SuperAdmin"))
        # else:
        #     self.stdout.write("Group already exists: SuperAdmin")

        # 2.定义业务类型
        admin_model = models.Admin
        employee_model = models.Employee
        department_model = models.Department
        task_model = models.TaskManage
        order_model = models.Order

        ### 3.SuperAdmin ###
        # 需要管理的Model
        superadmin_models = [
            admin_model,
            employee_model,
            department_model,
            task_model,
            order_model,
        ]

        # 分配每个Model的四种默认权限
        for model in superadmin_models:
            self.add_model_permissions(
                superadmin, model, ["add", "change", "delete", "view"]
            )
        # 自定义：管理员角色管理权限
        manage_admin_roles = Permission.objects.get(
            content_type__app_label="app01", codename="manage_admin_roles"
        )

        superadmin.permissions.add(manage_admin_roles)

        reset_admin_password = Permission.objects.get(
            content_type__app_label="app01",codename="reset_admin_password"
        )

        superadmin.permissions.add(reset_admin_password)
        ### 4.HRAdmin ###

        hr_models = [
            admin_model,
            employee_model,
            department_model,
        ]

        for model in hr_models:
            self.add_model_permissions(
                hr_admin, model, ["add", "change", "delete", "view"]
            )

        ### 5.BusinessAdmin ###
        business_models = [
            department_model,
            order_model,
            task_model,
        ]

        for model in business_models:
            self.add_model_permissions(
                business_admin, model, ["add", "change", "delete", "view"]
            )

        ### 6.ReadOnly ###
        readonly_models = [
            admin_model,
            employee_model,
            department_model,
            task_model,
            order_model,
        ]

        for model in readonly_models:
            self.add_model_permissions(readonly, model, ["view"])
        self.stdout.write(self.style.SUCCESS("RBAC 初始化完成"))

    # 给某Group授予权限的动作抽象封装成函数
    def add_model_permissions(self, group, model, actions):
        """
        给指定 Group 添加指定 Model 的
        add / change / delete / view 四种默认权限。
        """
        # 获取mdoel对应的ContentType
        content_type = ContentType.objects.get_for_model(model)
        for action in actions:
            
            codename = f"{action}_{model._meta.model_name}"
            permission = Permission.objects.get(
                content_type=content_type, codename=codename
            )

            # 将权限分配给SuperAdmin
            group.permissions.add(permission)

            self.stdout.write(
                f"Assigned {model._meta.model_name} permission to " f"{group.name}"
            )
