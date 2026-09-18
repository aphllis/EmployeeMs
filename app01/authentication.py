from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from app01 import models

class AdminSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        info=request.session.get('info')

        if not info:
            return None
        admin_id=info.get('id')

        try:
            admin_obj=models.Admin.objects.get(id=admin_id)
        except models.Admin.DoesNotExist:
            raise AuthenticationFailed("管理员账号不存在")
        #DRF 在viewset中会拿到这个返回值，并且令request.user = admin_obj
        # request.auth = None
        return (admin_obj,None)
    