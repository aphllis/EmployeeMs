from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app01 import models


class Command(BaseCommand):
    help = "Initialize RBAC roles and permissions"

    def handle(self, *args, **options):
          # 每个角色的模型权限。未列出的权限不会授予。
        role_model_permissions = {
            "SuperAdmin": [
                (models.Account, ["view"]),
            ],
            "HRAdmin": [
                (models.Account, ["view", "add", "change"]),
                (models.Employee, ["view", "add", "change"]),
                (models.Department, ["view", "add", "change"]),
                (models.Position, ["view", "add", "change"]),
            ],
            "BusinessAdmin": [
                (models.Order, ["view", "add", "change"]),
            ],
            "ProjectManager": [
                (models.TaskManage, ["view", "add", "change"]),
            ],
            # 暂时保留旧组，清掉它的通用读取权限。
            # 后续应按具体业务范围给只读用户授权。
            "ReadOnly": [],
        }

        # 只有 SuperAdmin 可以分配角色和强制重置密码。
        role_custom_permissions = {
            "SuperAdmin": [
                "manage_account_roles",
                "reset_account_password",
            ],
        }

        for group_name, model_rules in role_model_permissions.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            permissions = []

            for model, actions in model_rules:
                content_type = ContentType.objects.get_for_model(model)

                for action in actions:
                    codename = f"{action}_{model._meta.model_name}"
                    permission = Permission.objects.get(
                        content_type=content_type,
                        codename=codename,
                    )
                    permissions.append(permission)

            content_type = ContentType.objects.get_for_model(models.Account)

            for codename in role_custom_permissions.get(group_name, []):
                permission = Permission.objects.get(
                    content_type=content_type,
                    codename=codename,
                )
                permissions.append(permission)

            # 以本配置为准，同时撤销该组旧的多余权限。
            group.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{group_name}: 已设置 {len(permissions)} 项权限"
                )
            )

        self.stdout.write(self.style.SUCCESS("RBAC 初始化完成"))
    #     # 1.创建角色(此处即权限组Group)
    #     superadmin, _ = Group.objects.get_or_create(name="SuperAdmin")
    #     hr_admin, _ = Group.objects.get_or_create(name="HRAdmin")
    #     business_admin, _ = Group.objects.get_or_create(name="BusinessAdmin")
    #     readonly, _ = Group.objects.get_or_create(name="ReadOnly")


    #     # 2.定义业务类型
    #     account_model = models.Account
    #     employee_model = models.Employee
    #     department_model = models.Department
    #     task_model = models.TaskManage
    #     order_model = models.Order

    #     ### 3.SuperAdmin ###
    #     # 需要管理的Model
    #     superadmin_models = [
    #         account_model,
    #         employee_model,
    #         department_model,
    #         task_model,
    #         order_model,
    #     ]

    #     # 分配每个Model的四种默认权限
    #     for model in superadmin_models:
    #         self.add_model_permissions(
    #             superadmin, model, ["add", "change", "delete", "view"]
    #         )
    #     # 自定义：管理员角色管理权限
    #     manage_account_roles = Permission.objects.get(
    #         content_type__app_label="app01",
    #         content_type__model="account",
    #         codename="manage_account_roles",
    #     )

    #     superadmin.permissions.add(manage_account_roles)

    #     reset_account_password = Permission.objects.get(
    #         content_type__app_label="app01",
    #         content_type__model="account",
    #         codename="reset_account_password",
    #     )

    #     superadmin.permissions.add(reset_account_password)
    #     ### 4.HRAdmin ###

    #     hr_models = [
    #         account_model,
    #         employee_model,
    #         department_model,
    #     ]

    #     for model in hr_models:
    #         self.add_model_permissions(
    #             hr_admin, model, ["add", "change", "delete", "view"]
    #         )

    #     ### 5.BusinessAdmin ###
    #     business_models = [
    #         department_model,
    #         order_model,
    #         task_model,
    #     ]

    #     for model in business_models:
    #         self.add_model_permissions(
    #             business_admin, model, ["add", "change", "delete", "view"]
    #         )

    #     ### 6.ReadOnly ###
    #     readonly_models = [
    #         account_model,
    #         employee_model,
    #         department_model,
    #         task_model,
    #         order_model,
    #     ]

    #     for model in readonly_models:
    #         self.add_model_permissions(readonly, model, ["view"])
    #     self.stdout.write(self.style.SUCCESS("RBAC 初始化完成"))

    # # 给某Group授予权限的动作抽象封装成函数
    # def add_model_permissions(self, group, model, actions):
    #     """
    #     给指定 Group 添加指定 Model 的
    #     add / change / delete / view 四种默认权限。
    #     """
    #     # 获取model对应的ContentType
    #     content_type = ContentType.objects.get_for_model(model)
    #     for action in actions:

    #         codename = f"{action}_{model._meta.model_name}"
    #         permission = Permission.objects.get(
    #             content_type=content_type, codename=codename
    #         )

    #         # 将权限分配给SuperAdmin
    #         group.permissions.add(permission)

    #         self.stdout.write(
    #             f"Assigned {model._meta.model_name} permission to " f"{group.name}"
    #         )
