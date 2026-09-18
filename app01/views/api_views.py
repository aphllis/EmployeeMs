
from rest_framework import permissions, viewsets

from app01.serializers import  EmployeeSerializer,DepartmentSerializer
from app01.authentication import AdminSessionAuthentication
from app01.permissions import IsAdmin
from app01 import models


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = models.Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes=[AdminSessionAuthentication]
    permission_classes=[IsAdmin]
    # permission_classes = [permissions.IsAuthenticated]

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = models.Department.objects.all()
    serializer_class = DepartmentSerializer
    authentication_classes=[AdminSessionAuthentication]
    permission_classes=[IsAdmin]
    # permission_classes = [permissions.IsAuthenticated]
