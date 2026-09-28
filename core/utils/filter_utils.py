from django.db.models import Q


def split_list_param(value):
    """
    Splits a comma-separated query parameter into its values,
    ignoring surrounding whitespace and empty entries.
    """
    return [item.strip() for item in value.split(',') if item.strip()]


def any_iexact(field_name, values):
    """
    Matches rows where the field equals any of the values, ignoring
    case. Django has no case-insensitive __in lookup, and MySQL and
    PostgreSQL disagree on whether plain __in ignores case.

    With no values it matches nothing, like __in with an empty list.
    """
    if not values:
        return Q(pk__in=[])

    query = Q()
    for value in values:
        query |= Q(**{f'{field_name}__iexact': value})

    return query
