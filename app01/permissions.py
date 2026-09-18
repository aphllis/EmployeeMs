from rest_framework.permissions import BasePermission
from app01 import models

class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        #如果request.user不是models.Admin类，就不算管理员，返回False
        # print("request.user =", request.user)
        # print("user type =", type(request.user))
        return isinstance(request.user, models.Admin)