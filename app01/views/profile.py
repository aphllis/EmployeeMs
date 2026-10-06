from django.shortcuts import render,redirect

from app01 import models
from app01.utils.form import AdminChangePasswordForm
from app01.utils.permission import get_current_admin