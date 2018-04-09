# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Level(models.Model):
    """
    The level of a degree, e.g. Bachelor, Master, Doctorate
    """
    name = models.CharField(max_length=255, null=False, blank=False)

class Career(models.Model):
    """
    The career level of a degree, e.g. Undergraduate, Graduate
    """
    name = models.CharField(max_length=255, null=False, blank=False)

class Degree(models.Model):
    """
    The degree name conferred by a program, e.g. Bachelor of Science
    """
    name = models.CharField(max_length=255, null=False, blank=False)

class College(models.Model):
    """
    A college, including various names and urls
    """
    full_name = models.CharField(max_length=255, null=False, blank=False)
    short_name = models.CharField(max_length=255, null=True, blank=False)
    college_url = models.URLField(null=True, blank=True)
    profile_url = models.URLField(null=True, blank=True)

class Department(models.Model):
    """
    A department, including name and url
    """
    full_name = models.CharField(max_length=255, null=False, blank=False)
    department_url = models.CharField(max_length=255, null=True, blank=True)
    school = models.BooleanField(default=False, null=False, blank=False)

class ProgramProfileType(models.Model):
    """
    Types of program profiles, e.g. Main Site, UCF Online
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    root_url = models.URLField(null=False, blank=False)

class ProgramProfile(models.Model):
    """
    URLs to specific profile pages for programs
    """
    profile_type = models.ForeignKey(ProgramProfileType)
    url = models.URLField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)

class Program(models.Model):
    """
    A program of study and related meta fields
    """
    name = models.CharField(max_length=500, null=False, blank=False)
    plan_code = models.CharField(max_length=10, null=False, blank=False)
    subplan_code = models.CharField(max_length=10, null=True, blank=True)
    catalog_url = models.URLField(null=True, blank=True)
    colleges = models.ManyToManyField(College, blank=True)
    departments = models.ManyToManyField(Department, blank=True)
    level = models.ForeignKey(Level)
    career = models.ForeignKey(Career)
    degree = models.ForeignKey(Degree)
    program_profiles = models.ManyToManyField(ProgramProfile)

    @property
    def program_code(self):
        """
        Returns a truncated combination of the plan and subplan code
        """
        return self.plan_code + self.subplan_code

    @property
    def primary_profile_url(self):
        return self.program_profiles.get(primary=True)
