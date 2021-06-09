from django.db import models

from teledata.models import Organization as TeledataOrg
from teledata.models import Department as TeledataDept
from programs.models import College
from programs.models import Department as ProgramDept

# Create your models here.


class Organization(models.Model):
    """
    TODO
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    teledata = models.ForeignKey(TeledataOrg, related_name='organization_unit', on_delete=models.CASCADE)
    college = models.ForeignKey(College, related_name='organization_unit', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Department(models.Model):
    """
    TODO
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.SET_NULL)
    teledata = models.ForeignKey(TeledataDept, related_name='department_unit', on_delete=models.CASCADE)
    program_data = models.ForeignKey(ProgramDept, related_name='department_unit', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
