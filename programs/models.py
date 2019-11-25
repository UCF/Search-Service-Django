# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

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

class CollegeManager(models.Manager):
    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)


class College(models.Model):
    """
    A college, including various names and urls
    """
    objects = CollegeManager()

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

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Program(models.Model):
    """
    A program of study and related meta fields
    """
    name = models.CharField(max_length=500, null=False, blank=False)
    credit_hours = models.IntegerField(null=True, blank=True)
    plan_code = models.CharField(max_length=255, null=False, blank=False)
    subplan_code = models.CharField(max_length=255, null=True, blank=True)
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
    created = models.DateTimeField(auto_now_add=True, null=False)
    modified = models.DateTimeField(auto_now=True, null=False)
    resident_tuition = models.DecimalField(null=True, blank=True, max_digits=7, decimal_places=2)
    nonresident_tuition = models.DecimalField(null=True, blank=True, max_digits=7, decimal_places=2)
    tuition_types = [
        ('SCH', 'Single Credit Hour'),
        ('TRM', 'Term'),
        ('CRS', 'Course'),
        ('ANN', 'Annual')
    ]
    tuition_type = models.CharField(max_length=3, null=True, blank=True, choices=tuition_types)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('plan_code', 'subplan_code')

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
    program = models.ForeignKey(
        Program,
        null=False,
        blank=False,
        related_name='profiles'
    )

    class Meta:
        unique_together = ('profile_type', 'program')

    def __str__(self):
        return '{0} {1}'.format(self.program.name, self.profile_type.name)

    def __unicode__(self):
        return '{0} {1}'.format(self.program.name, self.profile_type.name)


class ProgramDescription(models.Model):
    """
    Program descriptions to be used on various sites
    """
    description_type = models.ForeignKey(ProgramDescriptionType)
    description = models.TextField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)
    program = models.ForeignKey(
        Program,
        null=False,
        blank=False,
        related_name='descriptions'
    )

    class Meta:
        unique_together = ('description_type', 'program')

    def __str__(self):
        return '{0} {1}'.format(self.program.name, self.description_type.name)

    def __unicode__(self):
        return '{0} {1}'.format(self.program.name, self.description_type.name)

class Fee(models.Model):
    fee_name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.fee_name

    def __unicode__(self):
        return self.fee_name

class TuitionOverride(models.Model):
    tuition_code = models.CharField(max_length=10, null=False, blank=False)
    plan_code = models.CharField(max_length=10, null=False, blank=False)
    subplan_code = models.CharField(max_length=10, null=True, blank=True)
    skip = models.BooleanField(default=False, null=False, blank=False)
    required_fees = models.ManyToManyField(Fee, blank=True)

    @property
    def program(self):
        program = Program.objects.filter(plan_code=self.plan_code, subplan_code=self.subplan_code)

        if len(program):
            return program[0]

        return None

    def __str__(self):
        program = Program.objects.filter(plan_code=self.plan_code, subplan_code=self.subplan_code)

        if len(program):
            return '{0} Tuition Override'.format(program[0].name)

        if self.subplan_code is not None:
            return '{0} {1} Tuition Override'.format(self.plan_code, self.subplan_code)

        return '{0} Tuition Override'.format(self.plan_code)

    def __unicode__(self):
        program = self.program

        if program is not None:
            return '{0} Tuition Override'.format(program.name)

        if self.subplan_code is not None:
            return '{0} {1} Tuition Override'.format(self.plan_code, self.subplan_code)

        return '{0} Tuition Override'.format(self.plan_code)

class CollegeOverride(models.Model):
    plan_code = models.CharField(max_length=10, null=False, blank=False)
    subplan_code = models.CharField(max_length=10, null=True, blank=True)
    college = models.ForeignKey(College, null=False, blank=False)

    @property
    def program(self):
        program = Program.objects.filter(plan_code=self.plan_code, subplan_code=self.subplan_code)

        if len(program):
            return program[0]

        return None

    def __str__(self):
        program = self.program

        if program is not None:
            return '{0} - {1} Override'.format(program.name, self.college.short_name)

        if self.subplan_code is not None:
            return '{0} {1} - {2} Override'.format(self.plan_code, self.subplan_code, self.college.short_name)

        return '{0} - {1} Tuition Override'.format(self.plan_code, self.college.short_name)

    def __unicode__(self):
        program = self.program

        if program is not None:
            return '{0} - {1} Override'.format(program.name, self.college.short_name)

        if self.subplan_code is not None:
            return '{0} {1} - {2} Override'.format(self.plan_code, self.subplan_code, self.college.short_name)

        return '{0} - {1} Tuition Override'.format(self.plan_code, self.college.short_name)

class AcademicYear(models.Model):
    code = models.CharField(max_length=4, null=False, blank=False)
    display = models.CharField(max_length=9, null=False, blank=False)

    def __unicode__(self):
        return self.code

    def __str__(self):
        return self.code


class ProgramOutcomeStat(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='outcomes')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='outcomes')
    employed_full_time = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    continuing_edication = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    avg_annual_earnings = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    def __unicode__(self):
        return "{0} Outcomes".format(self.program.name)

    def __str__(self):
        return "{0} Outcomes".format(self.program.name)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
