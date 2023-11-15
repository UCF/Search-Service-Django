# -*- coding: utf-8 -*-


from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from programs.models import College, Department, Program

# Create your models here.


class LowercaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(LowercaseCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super(LowercaseCharField, self).get_prep_value(value)
        if value is not None:
            return value.lower()
        return ''

class ExtendedUser(models.Model):
    user = models.OneToOneField(User, related_name='meta', on_delete=models.CASCADE)
    colleges_can_edit = models.ManyToManyField(College, blank=True, related_name='editors')
    departments_can_edit = models.ManyToManyField(Department, blank=True, related_name='editors')

    @property
    def editable_programs(self):
        """
        Returns all the programs the user
        has access to edit.
        """
        if self.user.is_superuser:
            return Program.objects.all()
        elif self.colleges_can_edit.count() == 0 or self.departments_can_edit.count() == 0:
            return Program.objects.none()
        else:
            return Program.objects.filter(
                models.Q(colleges__in=self.colleges_can_edit) |
                models.Q(departments__in=self.departments_can_edit)
            )

    @property
    def programs_missing_descriptions_count(self) -> int:
        """
        Returns the number of programs missing
        custom descriptions
        """
        return self.editable_programs.count() - self.editable_programs.filter(descriptions__description_type=settings.CUSTOM_DESCRIPTION_TYPE_ID).count()
