from django.conf import settings
from django.contrib.auth.models import User

# The short names pysaml2 gives Azure's claims when its ADFS attribute
# map applies. When it doesn't, the attributes keep their claim URIs,
# which ATTRIBUTES_MAP lists, so both are checked.
SAML_SHORT_NAMES = {
    'first_name': 'givenName',
    'last_name': 'surname',
    'email': 'emailAddress',
}


def _update_user(user: User, saml_data: dict):
    """
    Copies the name and email from the SAML attributes onto the user.
    A missing or empty claim leaves the field as it was, so a change to
    the claims in Azure can't block logins or blank out existing data.
    """
    attributes_map = settings.SAML2_AUTH.get('ATTRIBUTES_MAP', {})

    for field, short_name in SAML_SHORT_NAMES.items():
        values = saml_data.get(short_name) or saml_data.get(attributes_map.get(field)) or []

        if values and values[0]:
            setattr(user, field, values[0])

    user.save()


def on_saml_user_create(user: User, saml_data: dict):
    _update_user(user, saml_data)


def on_saml_before_login(user: User, saml_data: dict):
    _update_user(user, saml_data)
