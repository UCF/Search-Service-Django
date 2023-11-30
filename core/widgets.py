from decimal import Decimal
from typing import Any
from django import forms

class Wysiwyg(forms.Textarea):
    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if 'class' in attrs:
            cls = set(attrs['class'].split(' '))
            cls.add('wysiwyg')
            attrs['class'] = ' '.join(list(cls))
        else:
            attrs['class'] = 'wysiwyg'

        return attrs

    def use_required_attribute(self, initial: Any) -> bool:
        return True
