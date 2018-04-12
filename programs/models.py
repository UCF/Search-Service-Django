# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Level(models.Model):
    """
    The level of a degree, e.g. Bachelor, Master, Doctorate
    """
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Career(models.Model):
    """
    The career level of a degree, e.g. Undergraduate, Graduate
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    abbr = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Degree(models.Model):
    """
    The degree name conferred by a program, e.g. Bachelor of Science
    """
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class College(models.Model):
    """
    A college, including various names and urls
    """
    full_name = models.CharField(max_length=255, null=False, blank=False)
    short_name = models.CharField(max_length=255, null=True, blank=False)
    college_url = models.URLField(null=True, blank=True)
    profile_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name


class Department(models.Model):
    """
    A department, including name and url
    """
    full_name = models.CharField(max_length=255, null=False, blank=False)
    department_url = models.CharField(max_length=255, null=True, blank=True)
    school = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name

class ProgramProfileType(models.Model):
    """
    Types of program profiles, e.g. Main Site, UCF Online
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    root_url = models.URLField(null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class ProgramDescriptionType(models.Model):
    """
    Types of program descriptions, e.g. Main Site, UCF Online, Promotion
    """
    name = models.CharField(max_length=255, null=False, blank=False)


class Program(models.Model):
    """
    A program of study and related meta fields
    """
    name = models.CharField(max_length=500, null=False, blank=False)
    credit_hours = models.IntegerField(null=True, blank=True)
    plan_code = models.CharField(max_length=10, null=False, blank=False)
    subplan_code = models.CharField(max_length=10, null=True, blank=True)
    catalog_url = models.URLField(null=True, blank=True)
    colleges = models.ManyToManyField(College, blank=True)
    departments = models.ManyToManyField(Department, blank=True)
    level = models.ForeignKey(Level)
    career = models.ForeignKey(Career)
    degree = models.ForeignKey(Degree)
    online = models.BooleanField(null=False, blank=False, default=False)
    parent_program = models.ForeignKey('self',
                                       null=True,
                                       blank=True,
                                       related_name='subplans')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @property
    def program_code(self):
        """
        Returns a truncated combination of the plan and subplan code
        """
        return self.plan_code + self.subplan_code

    @property
    def primary_profile_url(self):
        return self.program_profiles.get(primary=True)

    @property
    def has_subplans(self):
        if len(self.subplans.all()) > 0:
            return True

        return False

    @property
    def is_subplan(self):
        if self.parent_program:
            return True

        return False

    @property
    def has_online(self):
        if self.subplans.filter(online=True).count() > 0:
            return True

        return False


class ProgramProfile(models.Model):
    """
    URLs to specific profile pages for programs
    """
    profile_type = models.ForeignKey(ProgramProfileType)
    url = models.URLField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)
    program = models.ForeignKey(Program, null=False, blank=False, related_name='profiles')

    def __str__(self):
        return '{0} {1}'.format(self.program.name, self.profile_type.name)

    def __unicode__(self):
        return '{0} {1}'.format(self.program.name, self.profile_type.name)

class ProgramDescription(models.Model):
    """
    Program descriptions to be used on various sites
    """
    profile_type = models.ForeignKey(ProgramDescriptionType)
    description = models.TextField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)
    program = models.ForeignKey(Program, null=False, blank=False, related_name='descriptions')
