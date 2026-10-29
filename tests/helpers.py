from django.contrib.auth.models import Group,Permission

# 辅助函数，增加api v2测试入口的账号权限
def grant_model_permission(account,model_name,*actions):
    group=Group.objects.create(
        name=f"pytest_{account.pk}_{model_name}"
    )
    codenames=[f"{action}_{model_name}" for action in actions]
    permissions=Permission.objects.filter(
        content_type__app_label="app01",
        content_type__model=model_name,
        codename__in=codenames
    )
    assert permissions.count()==len(codenames)

    group.permissions.add(*permissions)
    account.groups.add(group)