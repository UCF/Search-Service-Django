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


@register.filter(is_safe=True)
def check(value):
    if value == True:
        return f'<span class="fa fa-check-circle text-success" aria-hidden="true"><span><span class="sr-only">{ value }</span>'
    elif value == False:
        return f'<span class="fa fa-times-circle text-danger" aria-hidden="true"><span><span class="sr-only">{ value }</span>'

    return ''

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

@register.inclusion_tag('templatetags/auditlog-event.html')
def auditlog_event(**kwargs):
    event = kwargs.get('event', None)

    if event is None:
        return None

    action = ''
    if event.action == 0:
        action = 'Created'
    elif event.action == 1:
        action = 'Updated'
    elif event.action == 2:
        action = 'Deleted'

    content_type = event.content_type.name

    ctx = {
        'action': action,
        'content_type': content_type,
        'name': event.object_repr
    }

    return ctx
