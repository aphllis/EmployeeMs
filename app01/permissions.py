from rest_framework.permissions import BasePermission
from app01 import models


# class IsAdmin(BasePermission):

#     def has_permission(self, request, view):
#         # 如果request.user不是models.Admin类，就不算管理员，返回False
#         # print("request.user =", request.user)
#         # print("user type =", type(request.user))
#         return isinstance(request.user, models.Account)


class HasAccountModelPermission(BasePermission):
    message = "账号没有执行此操作的权限"
    action_to_permission = {
        "list": "view",
        "retrieve": "view",
        "create": "add",
        "update": "change",
        "partial_update": "change",
        "destroy": "delete",
    }

    def has_permission(self, request, view):
        account = request.user
        if not account or not getattr(account, "is_active", False):
            return False
        action = getattr(view, "action", None)
        permission_action = self.action_to_permission.get(action)
        if permission_action is None:
            return False
        # view.get_queryset()获取当前视图对应模型的queryset譬如Employee.objects.all(),然后.model获取该模型类
        # 也可以view.queryset.model
        model = view.get_queryset().model
        permission_name = (
            f"{model._meta.app_label}." f"{permission_action}_{model._meta.model_name}"
        )
        return account.has_perm(permission_name)
