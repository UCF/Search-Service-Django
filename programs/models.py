# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import re

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


class CIPVersionManager(models.Manager):
    def get_queryset(self):
        return super(CIPVersionManager, self).get_queryset().filter(version=settings.CIP_CURRENT_VERSION)


class CIP(models.Model):
    versions = [
        ('2010', '2010'),
        ('2020', '2020')
    ]

    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    version = models.CharField(max_length=4, null=False, blank=False, choices=versions, default=settings.CIP_CURRENT_VERSION)
    code = models.CharField(max_length=7, null=False, blank=False)
    area = models.IntegerField(null=False, blank=True)
    subarea = models.IntegerField(null=True, blank=True)
    precise = models.IntegerField(null=True, blank=True)

    objects = models.Manager()
    current_version = CIPVersionManager()
    next_version = models.OneToOneField('self', null=True, blank=True, related_name='previous_version')

    def save(self, *args, **kwargs):
        if self.code is not None:
            matches = re.match('^(?P<area>\d{2})\.?(?P<subarea>\d{2})?(?P<precise>\d{2})?$', self.code).groupdict()
            self.area = int(matches['area'])
            self.subarea = int(matches['subarea']) if matches['subarea'] is not None else 0
            self.precise = int(matches['precise']) if matches['precise'] is not None else 0

        super(CIP, self).save(*args, **kwargs)

    def __unicode__(self):
        return "{0} - {1} ({2})".format(
            str(self.code),
            self.name,
            self.version
        )

    def __str__(self):
        return "{0} - {1} ({2})".format(
            str(self.code),
            self.name,
            self.version
        )

class JobPosition(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

class SOC(models.Model):
    versions = [
        ('2010', '2010'),
    ]

    name = models.CharField(max_length=255, null=False, blank=False)
    code = models.CharField(max_length=7, null=False, blank=False)
    version = models.CharField(max_length=4, null=False, blank=False, choices=versions, default=settings.SOC_CURRENT_VERSION)
    cip = models.ManyToManyField(CIP, related_name='occupations')
    jobs = models.ManyToManyField(JobPosition, related_name='occupations')

    def __unicode__(self):
        return "{0} - {1}".format(self.name, self.code)

    def __str__(self):
        return "{0} - {1}".format(self.name, self.code)


class EmploymentProjection(models.Model):
    report_years = [
        ('1828', '2018-2028'),
    ]

    soc = models.ForeignKey(SOC, on_delete=models.CASCADE, related_name='projections')
    report = models.CharField(max_length=4, default=settings.PROJ_CURRENT_REPORT, choices=report_years, null=False, blank=False)
    begin_employment = models.IntegerField(null=False, blank=False)
    end_employment = models.IntegerField(null=False, blank=False)
    change = models.IntegerField(null=False, blank=False)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False)
    openings = models.IntegerField(null=False, blank=False)

    def __unicode__(self):
        return '{0} - {1} Projections'.format(self.soc.name, self.report)

    def __str__(self):
        return '{0} - {1} Projections'.format(self.soc.name, self.report)

    @property
    def report_year_begin(self):
        return '20{0}'.format(self.report[:2])

    @property
    def report_year_end(self):
        return '20{0}'.format(self.report[2:4])

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

class AcademicYear(models.Model):
    code = models.CharField(max_length=4, null=False, blank=False)
    display = models.CharField(max_length=9, null=False, blank=False)

    def __unicode__(self):
        return self.display

    def __str__(self):
        return self.display


class ProgramOutcomeStat(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='outcomes')
    cip = models.ForeignKey(CIP, on_delete=models.CASCADE, related_name='outcomes')
    employed_full_time = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    continuing_education = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    avg_annual_earnings = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    def __unicode__(self):
        return "{0} Outcomes - {1}".format(self.cip.code, self.academic_year.display)

    def __str__(self):
        return "{0} Outcomes {1}".format(self.cip.code, self.academic_year.display)

class Program(models.Model):
    """
    A program of study and related meta fields
    """
    name = models.CharField(max_length=500, null=False, blank=False)
    credit_hours = models.IntegerField(null=True, blank=True)
    plan_code = models.CharField(max_length=255, null=False, blank=False)
    subplan_code = models.CharField(max_length=255, null=True, blank=True)
    cip = models.ManyToManyField(CIP, blank=True)
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
    outcomes = models.ManyToManyField(ProgramOutcomeStat, related_name='programs')
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

    @property
    def current_cip(self):
        try:
            return self.cip.get(version=settings.CIP_CURRENT_VERSION)
        except CIP.DoesNotExist:
            return None

    @property
    def current_occupations(self):
        if self.current_cip:
            return self.current_cip.occupations.filter(version=settings.SOC_CURRENT_VERSION)
        else:
            return None

    @property
    def current_projections(self):
        projections = EmploymentProjection.objects.filter(soc__in=self.current_occupations, report=settings.PROJ_CURRENT_REPORT).distinct()
        return projections

    @property
    def careers(self):
        retval = []
        for occupation in self.current_occupations:
            for job in occupation.jobs.all():
                if job.name not in retval:
                    retval.append(job.name)

        return retval


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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
