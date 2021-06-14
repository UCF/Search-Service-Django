from django.db import models

# Create your models here.


class OrganizationUnit(models.Model):
    """
    TODO
    """
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class DepartmentUnit(models.Model):
    """
    TODO
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    organization_unit = models.ForeignKey(OrganizationUnit, related_name='department_units', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
