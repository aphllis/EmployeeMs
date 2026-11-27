from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from app01 import models
from app01.utils.form import ProjectPathTemplateForm
from app01.utils.pagination import Pagination
from app01.utils.permission import account_permission, get_current_account


@account_permission("app01.view_projectpathtemplate")
def project_path_template_lst(req):
    """列出公共路径模板；普通员工可以查看，有管理权限者可以维护"""
    search = req.GET.get("q", "").strip()
    queryset = models.ProjectPathTemplate.objects.all()

    if search:
        queryset = queryset.filter(
            models.Q(name__icontains=search)
            | models.Q(relative_path__icontains=search)
            | models.Q(note__icontains=search)
        )
    if queryset.exists():
        page = Pagination(request=req, queryset=queryset, page_size=20)
        page_queryset = page.page_queryset
        page_str, goto_page_str = page.html()
    else:
        page_queryset = []
        page_str = ""
        goto_page_str = ""

    account = get_current_account(req)
    return render(
        req,
        "project_path_template_lst.html",
        {
            "queryset": page_queryset,
            "search": search,
            "page_str": page_str,
            "goto_page_str": goto_page_str,
            "can_add": account.has_perm("app01.add_projectpathtemplate"),
            "can_change": account.has_perm("app01.change_projectpathtemplate"),
        },
    )

@require_http_methods(["GET","POST"])
@account_permission("app01.add_projectpathtemplate")
def project_path_template_add(req):
    form =ProjectPathTemplateForm(data=req.POST or None)
    if req.method=="POST" and form.is_valid():
        template=form.save(commit=False)
        template.created_by=get_current_account(req)
        template.save()
        return redirect("project_path_template_lst")
    return render(
        req,
        "form.html",
        {
            "form":form,
            "page_title":"新建公共路径模版",
            "submit_label":"保存模版",
            "cancel_url":reverse("project_path_template_lst"),
            "form_max_width":"55rem",
        }
    )
@require_http_methods(["GET", "POST"])
@account_permission("app01.change_projectpathtemplate")
def project_path_template_edit(req, nid):
    template = get_object_or_404(models.ProjectPathTemplate, pk=nid)
    form = ProjectPathTemplateForm(
        data=req.POST or None,
        instance=template,
    )

    if req.method == "POST" and form.is_valid():
        form.save()
        return redirect("project_path_template_lst")

    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "编辑公共路径模板",
            "submit_label": "保存修改",
            "cancel_url": reverse("project_path_template_lst"),
            "cancel_label": "返回模板列表",
            "form_max_width": "55rem",
        },
    )


@require_POST
@account_permission("app01.change_projectpathtemplate")
def project_path_template_status(req, nid):
    """停用模板而不删除；既有项目路径不受影响。"""
    template = get_object_or_404(models.ProjectPathTemplate, pk=nid)
    active_value = req.POST.get("is_active")

    if active_value not in {"true", "false"}:
        return HttpResponseBadRequest("无效的模板状态")

    template.is_active = active_value == "true"
    template.save(update_fields=["is_active", "updated_at"])
    return redirect("project_path_template_lst")
