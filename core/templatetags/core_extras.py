from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    ctx = context['request'].GET.copy()
    for key, val in kwargs.items():
        ctx[key] = val
    for key in [key for key, val in ctx.items() if not val]:
        del ctx[key]
    return ctx.urlencode()

@register.inclusion_tag('templatetags/sortable-field-heading.html', takes_context=True)
def sortable_field_header(context, **kwargs):
    ctx = context['request'].GET.copy()
    current_order = ctx.get('order', None)
    field = kwargs.get('field')
    fieldname = kwargs.get('fieldname')

    retval = {
        'fieldname': fieldname,
        'field': field,
        'show_caret': False
    }

    if current_order in [field, f"-{field}"]:
        retval['field'] = field if current_order.startswith('-') else f"-{field}"
        retval['order'] = 'up' if current_order.startswith('-') else 'down'
        retval['show_caret'] = True

    return {**context.flatten(), **retval}