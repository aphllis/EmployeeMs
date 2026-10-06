from django.contrib.auth.backends import BaseBackend

class AdminPermissionBackend(BaseBackend):

    def has_perm(self, user_obj, perm, obj = ...):
        if not user_obj:
            return False

        # 当前Admin所属的所有Group
        groups = user_obj.groups.all()

        # 遍历Group
        for group in groups:
            # Group所拥有的权限
            if group.permissions.filter(
                content_type__app_label=perm.split('.')[0],
                codename=perm.split('.')[1]
            ).exists():
                return True
        return False