from django.contrib.auth.models import User

def on_saml_user_create(user: User, saml_data: dict):
    user.first_name = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname']
    user.last_name = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname']
    user.email = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress']
    user.save()

def on_saml_before_login(user: User, saml_data: dict):
    user.first_name = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname']
    user.last_name = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname']
    user.email = saml_data['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress']

    user.save()
