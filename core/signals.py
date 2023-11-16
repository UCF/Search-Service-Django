from django.contrib.auth.models import User
from core.models import ExtendedUser

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def on_user_post_save(sender, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created', False)
    if created:
        ExtendedUser.objects.create(user=instance).save()
