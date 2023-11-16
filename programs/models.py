# -*- coding: utf-8 -*-
from django.db import models
from django_mysql.models import ListTextField
import calendar
import re

from django.conf import settings
from django.utils.text import Truncator
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from units.models import Unit
from units.models import College as UnitCollege
from units.models import Department as UnitDepartment

from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

from bs4 import BeautifulSoup

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
    unit = models.OneToOneField(Unit, related_name='college', blank=True, null=True, on_delete=models.SET_NULL)
    unit_college = models.OneToOneField(UnitCollege, related_name='program_college', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name

    @property
    def name(self):
        if self.unit_college:
            return self.unit_college.name
        return self.full_name


class Department(models.Model):
    """
    A department, including name and url
    """
    full_name = models.CharField(max_length=255, null=False, blank=False)
    department_url = models.CharField(max_length=255, null=True, blank=True)
    school = models.BooleanField(default=False, null=False, blank=False)
    unit = models.ForeignKey(Unit, related_name='program_departments', blank=True, null=True, on_delete=models.SET_NULL)
    unit_department = models.ForeignKey(UnitDepartment, related_name='program_department', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name

    @property
    def name(self):
        if self.unit_department:
            return self.unit_department.name
        return self.full_name


class CIPVersionManager(models.Manager):
    def get_queryset(self):
        return super(CIPVersionManager, self).get_queryset().filter(version=settings.CIP_CURRENT_VERSION)


class CIP(models.Model):
    versions = settings.CIP_AVAILABLE_VERSIONS

    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    version = models.CharField(max_length=4, null=False, blank=False, choices=versions, default=settings.CIP_CURRENT_VERSION)
    code = models.CharField(max_length=7, null=False, blank=False)
    area = models.IntegerField(null=False, blank=True)
    subarea = models.IntegerField(null=True, blank=True)
    precise = models.IntegerField(null=True, blank=True)

    objects = models.Manager()
    current_version = CIPVersionManager()
    next_version = models.OneToOneField('self', null=True, blank=True, related_name='previous_version', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.code is not None:
            matches = re.match('^(?P<area>\d{2})\.?(?P<subarea>\d{2})?(?P<precise>\d{2})?$', self.code).groupdict()
            self.area = int(matches['area'])
            self.subarea = int(matches['subarea']) if matches['subarea'] is not None else 0
            self.precise = int(matches['precise']) if matches['precise'] is not None else 0

        super(CIP, self).save(*args, **kwargs)

    @property
    def area_code_str(self) -> str:
        """
        Returns the CIP area code as a string with a
        leading zero if necessary. Returns an empty
        string if the code is not set.
        """
        return str(self.area).zfill(2) if self.area is not None else ""

    @property
    def subarea_code_str(self) -> str:
        """
        Returns the CIP subarea code as a string with a
        leading zero if necessary. Returns an empty
        string if the code is not set.
        """
        return str(self.subarea).zfill(2) if self.subarea is not None else ""

    @property
    def precise_code_str(self) -> str:
        """
        Returns the CIP precise code as a string with a
        leading zero if necessary. Returns an empty
        string if the code is not set.
        """
        return str(self.precise).zfill(2) if self.precise is not None else ""


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
    versions = settings.SOC_AVAILABLE_VERSIONS

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
    report_years = settings.PROJ_AVAILABLE_REPORTS

    soc = models.ForeignKey(SOC, related_name='projections', on_delete=models.CASCADE)
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

class ProgramDescriptionTypeManager(models.Manager):

    @property
    def excerpt_description_type(self):
        try:
            return self.get(name=settings.EXCERPT_DESCRIPTION_TYPE_SOURCE)
        except ProgramDescription.DoesNotExist:
            return None


class ProgramDescriptionType(models.Model):
    """
    Types of program descriptions, e.g. Main Site, UCF Online, Promotion
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    objects = ProgramDescriptionTypeManager()

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
    academic_year = models.ForeignKey(AcademicYear, related_name='outcomes', on_delete=models.CASCADE)
    cip = models.ForeignKey(CIP, related_name='outcomes', on_delete=models.CASCADE)
    employed_full_time = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    continuing_education = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    avg_annual_earnings = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    def __unicode__(self):
        return "{0} Outcomes - {1}".format(self.cip.code, self.academic_year.display)

    def __str__(self):
        return "{0} Outcomes {1}".format(self.cip.code, self.academic_year.display)


class AdmissionTerm(models.Model):
    """
    Describes a term of admission, e.g. Fall, Spring, Summer
    """
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class AdmissionDeadlineType(models.Model):
    """
    Describes a type of program admission deadline,
    e.g. Domestic, International, Transfer
    """
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class ApplicationDeadline(models.Model):
    admission_term = models.ForeignKey(AdmissionTerm, related_name='application_deadlines', on_delete=models.CASCADE)
    career = models.ForeignKey(Career, related_name='application_deadlines', on_delete=models.CASCADE)
    deadline_type = models.ForeignKey(AdmissionDeadlineType, related_name='application_deadlines', on_delete=models.CASCADE)
    month = models.IntegerField(null=False, blank=False, choices=[(i, i) for i in range(1, 13)])
    day = models.IntegerField(null=False, blank=False, choices=[(i, i) for i in range(1, 32)])

    def __str__(self):
        return '{0} {1} {2}: {3}'.format(
            self.career.name,
            self.deadline_type.name,
            self.admission_term.name,
            self.display
        )

    def __unicode__(self):
        return '{0} {1} {2}: {3}'.format(
            self.career.name,
            self.deadline_type.name,
            self.admission_term.name,
            self.display
        )

    @property
    def display(self):
        """
        Returns a human friendly formatted version of the deadline date
        """
        return '{0} {1}'.format(
            calendar.month_name[self.month],
            self.day
        )

class AcademicTerm(models.Model):
    full_name = models.CharField(max_length=15, null=False, blank=False)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name

    @property
    def full_name_split(self):
        return self.full_name.split(' ')

    @property
    def semester(self):
        return self.full_name_split[0]

    @property
    def semester_index(self):
        if self.semester == 'Spring':
            return 0
        elif self.semester == 'Summer':
            return 1
        elif self.semester == 'Fall':
            return 2

        return None

    @property
    def year_as_str(self):
        if len(self.full_name_split) > 1:
            return self.full_name_split[1]
        return "9999"

    @property
    def year(self):
        return int(self.year_as_str)

    def __eq__(self, other):
        """
        Custom equal to operator
        """
        if not other:
            return False
        return self.semester == other.semester and self.year == other.year

    def __lt__(self, other):
        """
        Custom less than operator
        """
        if self.year < other.year:
            return True
        elif self.year == other.year:
            return self.semester_index < other.semester_index

        return False

    def __le__(self, other):
        """
        Custom less than or equal to operator
        """
        if self.year < other.year:
            return True
        elif self.year == other.year:
            return self.semester_index <= other.semester_index

        return False

    def __gt__(self, other):
        """
        Custom greater than operator
        """
        if self.year > other.year:
            return True
        elif self.year == other.year:
            return self.semester_index > other.semester_index

        return False

    def __ge__(self, other):
        """
        Custom greater than or equal to operator
        """
        if self.year > other.year:
            return True
        elif self.year == other.year:
            return self.semester_index >= other.semester_index

        return False

    def __ne__(self, other):
        """
        Custom not equal operator
        """
        return self.year != other.year or self.semester_index != other.semester_index

    def __sub__(self, other):
        """
        Custom subtraction operator for terms.
        Use subtractions to calculate the number of
        terms between one term and another.
        """
        retval = 0
        retval += (self.year - other.year) * 3
        retval += (self.semester_index - other.semester_index)
        return retval


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
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE)
    online = models.BooleanField(null=False, blank=False, default=False)
    parent_program = models.ForeignKey('self',
                                       null=True,
                                       blank=True,
                                       related_name='subplans',
                                       on_delete=models.CASCADE)
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
    outcomes = models.ManyToManyField(
        ProgramOutcomeStat,
        related_name='programs',
        blank=True
    )
    application_deadlines = models.ManyToManyField(ApplicationDeadline, blank=True, related_name='programs')
    application_requirements = ListTextField(
        base_field=models.CharField(max_length=255),
        size=20,  # max number of list items to store
        null=True,
        blank=True
    )
    active = models.BooleanField(default=True)
    active_comments = models.CharField(max_length=500, null=True, blank=True)
    active_comments_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    graduate_slate_id = models.CharField(max_length=255, null=True, blank=True)
    valid = models.BooleanField(default=True)
    has_locations = models.BooleanField(default=True)
    start_term = models.ForeignKey(AcademicTerm, null=True, blank=True, related_name='start_term_programs', on_delete=models.SET_NULL)
    history = AuditlogHistoryField()

    class Meta:
        unique_together = ('plan_code', 'subplan_code')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @property
    def excerpt(self) -> str:
        try:
            desc = self.descriptions.get(description_type=ProgramDescriptionType.objects.excerpt_description_type)
            soup = BeautifulSoup(desc.description, features='lxml')
            return Truncator(soup.get_text()).words(25, '...')

        except ProgramDescription.DoesNotExist:
            return '';

    @property
    def program_code(self):
        """
        Returns a truncated combination of the plan and subplan code
        """
        return self.plan_code + self.subplan_code

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
    def current_cip(self) -> CIP:
        try:
            return self.cip.get(version=settings.CIP_CURRENT_VERSION)
        except CIP.DoesNotExist:
            return None

    @property
    def current_occupations(self):
        if self.current_cip:
            return self.current_cip.occupations.filter(version=settings.SOC_CURRENT_VERSION)
        else:
            return SOC.objects.none()

    @property
    def current_projections(self):
        if self.current_occupations.count() > 0:
            projections = EmploymentProjection.objects.filter(soc__in=self.current_occupations, report=settings.PROJ_CURRENT_REPORT).distinct()
            return projections
        else:
            return EmploymentProjection.objects.none()

    @property
    def careers(self):
        return JobPosition.objects.filter(
            pk__in=self.current_occupations.filter(jobs__isnull=False).values_list('jobs', flat=True).distinct()
        )

    @property
    def primary_profile_type(self):
        rules = settings.PROGRAM_PROFILE

        retval = None

        for rule in rules:
            conditions_met = False

            # If there are no conditions, then the conditions are met.
            # This should only apply to the 'default' assignment.
            if len(rule['conditions']) < 1:
                conditions_met = True

            for condition in rule['conditions']:
                field_obj = Program._meta.get_field(condition['field'])
                field_val = field_obj.value_from_object(self)
                if field_val == condition['value']:
                    conditions_met = True

            if conditions_met == True:
                try:
                    profile_type = ProgramProfileType.objects.get(name=rule['value'])
                    return profile_type
                except:
                    continue

        return None

    @property
    def primary_profile_url(self):
        primary_profile = self.profiles.filter(primary=True).first()

        if primary_profile:
            return primary_profile.url
        else:
            primary_profile_type = self.primary_profile_type

            if primary_profile_type:
                fallback_profile = self.profiles.filter(profile_type=primary_profile_type).first()

                if fallback_profile:
                    return fallback_profile.url
                else:
                    return primary_profile_type.root_url

        return None

    @property
    def has_descriptions(self):
        return self.descriptions.count() > 0

    @property
    def has_custom_description(self):
        return self.descriptions.filter(description_type=settings.CUSTOM_DESCRIPTION_TYPE_ID).count() > 0


class ProgramProfile(models.Model):
    """
    URLs to specific profile pages for programs
    """
    profile_type = models.ForeignKey(ProgramProfileType, on_delete=models.CASCADE)
    url = models.URLField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)
    program = models.ForeignKey(
        Program,
        null=False,
        blank=False,
        related_name='profiles',
        on_delete=models.CASCADE
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
    description_type = models.ForeignKey(ProgramDescriptionType, on_delete=models.CASCADE)
    description = models.TextField(null=False, blank=False)
    primary = models.BooleanField(default=False, null=False, blank=False)
    program = models.ForeignKey(
        Program,
        null=False,
        blank=False,
        related_name='descriptions',
        on_delete=models.CASCADE
    )
    history = AuditlogHistoryField()

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
    skip = models.BooleanField(default=False, null=False, blank=False,
        help_text="The tuition values for the program will not be updated during the tuition import when this is checked.")
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
    college = models.ForeignKey(College, null=False, blank=False, on_delete=models.CASCADE)

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


class WeightedJobPosition(models.Model):
    program = models.ForeignKey(Program, related_name='weighted_jobs', on_delete=models.CASCADE)
    job = models.ForeignKey(JobPosition, related_name='weighted_positions', on_delete=models.CASCADE)
    weight = models.FloatField(null=False, blank=False, default=0.0)

    def __str__(self):
        return f"{self.program.name} - {self.career.name}"


auditlog.register(Program, serialize_data=True)
auditlog.register(ProgramDescription, serialize_data=True)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
