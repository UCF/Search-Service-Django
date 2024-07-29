# -*- coding: utf-8 -*-


from django.db import models
from django.db.models import Count
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
        elif self.colleges_can_edit.count() == 0 and self.departments_can_edit.count() == 0:
            return Program.objects.none()
        else:
            return Program.objects.filter(
                models.Q(colleges__in=self.colleges_can_edit.all()) |
                models.Q(departments__in=self.departments_can_edit.all())
            )


    @property
    def programs_missing_descriptions(self):
        """
        Returns the programs missing a description
        """
        return self.editable_programs.annotate(
            num_descriptions=Count('descriptions')
        ).filter(num_descriptions=0)


    @property
    def programs_missing_descriptions_count(self) -> int:
        """
        Returns the number of programs that have
        no programs.
        """
        return self.programs_missing_descriptions.count()


    @property
    def programs_with_custom_descriptions(self):
        """
        Returns all programs the user has access to edit
        that have custom descriptions
        """
        return self.editable_programs.filter(
            descriptions__description_type=settings.CUSTOM_DESCRIPTION_TYPE_ID
        )


    @property
    def programs_missing_custom_description(self):
        """
        Returns the programs missing custom descriptions
        """
        return self.editable_programs.exclude(id__in=self.programs_with_custom_descriptions)


    @property
    def programs_missing_custom_descriptions_count(self) -> int:
        """
        Returns the number of programs missing
        custom descriptions
        """
        return self.programs_missing_custom_description.count()


    @property
    def programs_missing_jobs(self):
        """
        Returns the programs missing career paths
        """
        return self.editable_programs.annotate(
            num_jobs=Count('jobs')
        ).filter(num_jobs=0)


    @property
    def programs_missing_jobs_count(self) -> int:
        """
        Returns the number of programs missing
        custom career paths
        """
        return self.programs_missing_jobs.count()

    @property
    def display_name_full(self) -> str:
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        else:
            return self.user.username
