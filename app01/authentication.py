from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from app01 import models

class AccountSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        info=request.session.get('info')

        if not info:
            return None
        account_id=info.get('account_id')
        if not account_id:
            raise AuthenticationFailed("登录信息缺少 Account ID")
        account=models.Account.objects.filter(pk=account_id).first()
        if account is None:
            raise AuthenticationFailed("账号不存在")

        if not account.is_active:
            raise AuthenticationFailed("账号已被禁用")
        #DRF 在viewset中会拿到这个返回值
        # 并且令request.user = admin_obj
        # request.auth = None
        return account,None
    