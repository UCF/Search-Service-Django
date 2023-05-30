from django.contrib.auth.models import User

def on_saml_user_create(user: User, saml_data: dict):
    user.first_name = saml_data['givenName']
    user.last_name = saml_data['surname']
    user.email = saml_data['emailAddress']
    user.save()

def on_saml_before_login(user: User, saml_data: dict):
    user.first_name = saml_data['givenName']
    user.last_name = saml_data['surname']
    user.email = saml_data['emailAddress']
    user.save()
