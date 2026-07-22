from django import forms


class Bootstrap:
    bootstrap_exclude_fields = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 插件添加样式的循环写法(利用django的forms源码)
        for name,field in self.fields.items():
            if name in self.bootstrap_exclude_fields:
                field.widget.attrs['class'] = 'mb-2'
                continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control mb-2'
                field.widget.attrs['placeholder'] = field.label
            else:
                field.widget.attrs = {
                    'class': 'form-control mb-2',
                    'placeholder': field.label
                }


class BootstrapModelForm(Bootstrap, forms.ModelForm):
    pass


class BootstrapForm(Bootstrap, forms.Form):
    pass
