# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q, When, Case, Value
from django_mysql.models import QuerySet
from django_mysql.models import QuerySetMixin

class Building(models.Model):
    objects = QuerySet.as_manager()

    name = models.CharField(max_length=255, null=True, blank=True)
    descr = models.CharField(max_length=255, null=True, blank=True)
    abrev = models.CharField(max_length=255, null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

class Organization(models.Model):
    objects = QuerySet.as_manager()

    name = models.CharField(max_length=255, null=True, blank=True)
    bldg = models.ForeignKey(Building, on_delete=models.CASCADE)
    room = models.CharField(max_length=50, null=True, blank=True)
    postal = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    fax = models.CharField(max_length=50, null=True, blank=True)
    primary_comment = models.TextField(null=True, blank=True)
    secondary_comment = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

class Department(models.Model):
    objects = QuerySet.as_manager()

    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    list_order = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    bldg = models.ForeignKey(Building, on_delete=models.CASCADE)
    room = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    fax = models.CharField(max_length=50, null=True, blank=True)
    primary_comment = models.TextField(null=True, blank=True)
    secondary_comment = models.TextField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

# Create your models here.
class Staff(models.Model):
    objects = QuerySet.as_manager()

    alpha = models.BooleanField(default=True, null=False, blank=False)
    last_name = models.CharField(max_length=25, null=False, blank=False)
    suffix = models.CharField(max_length=3, null=True, blank=True)
    name_title = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=14, null=False, blank=False)
    middle = models.CharField(max_length=15, null=True, blank=True)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    job_position = models.CharField(max_length=100, null=True, blank=True)
    bldg = models.ForeignKey(Building, on_delete=models.CASCADE)
    room = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=50, null=True, blank=True)
    email_machine = models.CharField(max_length=255, null=True, blank=True)
    postal = models.CharField(max_length=10, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    listed = models.BooleanField(default=True, null=False, blank=False)
    cellphone = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)

    @property
    def full_name_formatted(self):
        retval = self.last_name

        if self.suffix:
            retval += ' {0}'.format(self.suffix)

        retval += ','

        if self.name_title:
            retval += ' {0}'.format(self.name_title)

        retval += ' {0}'.format(self.first_name)

        if self.middle:
            retval += ' {0}'.format(self.middle)

        return retval

    @property
    def name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    @property
    def sort_name(self):
        return '{0} {1}'.format(self.last_name, self.first_name)

    def __unicode__(self):
        return self.full_name_formatted()

    def __str__(self):
        return self.full_name_formatted()

class CombinedTeledataViewManager(models.Manager, QuerySetMixin):
    """
    Custom manager that allows for special queries
    and update methods
    """
    def score(self, search):
        return Case(
            When(name=search, then=Value(30)),
            When(phone=search, then=Value(15)),
            When(first_name=search, then=Value(13)),
            When(last_name=search, then=Value(13)),
            When(name__sounds_like=search, then=Value(12)),
            When(last_name__sounds_like=search, then=Value(8)),
            When(first_name__sounds_like=search, then=Value(3)),
            When(department=search, then=Value(3)),
            When(organization=search, then=Value(3)),
            When(department__contains=search, then=Value(2)),
            When(organization__contains=search, then=Value(2)),
            When(name__contains=search, then=Value(1)),
            default=Value(0),
            output_field=models.IntegerField()
        )

    def search(self, **kwargs):
        s = ''
        if 'search' in kwargs:
            s = kwargs['search']

        queryset = self.annotate(
            score=self.score(s)
        ).filter(
            score__gt=0
        ).order_by(
            '-score'
        )

        return queryset

    def update_data(self):
        """
        Causes the table to retrieve data from the various
        aggregate tables
        """
        staff = Staff.objects.all()
        orgs  = Organization.objects.all()
        depts = Department.objects.all()

        self.all().delete()

        for s in staff:
            record = CombinedTeledataView(
                alpha=s.alpha,
                name=s.name,
                first_name=s.first_name,
                last_name=s.last_name,
                sort_name=s.sort_name,
                email=s.email,
                phone=s.phone,
                postal=s.postal,
                job_position=s.job_position,
                department=s.dept.name,
                dept_id=s.dept.id,
                organization=s.dept.org.name,
                org_id=s.dept.org.id,
                building=s.bldg.name,
                bldg_id=s.bldg.id,
                room=s.room,
                from_table='staff'
            )

            record.save(doing_import=True)

        for o in orgs:
            record = CombinedTeledataView(
                name=o.name,
                sort_name=o.name,
                phone=o.phone,
                fax=o.fax,
                building=o.bldg.name,
                bldg_id=o.bldg.id,
                room=o.room,
                from_table='organizations'
            )

            record.save(doing_import=True)

        for d in depts:
            record = CombinedTeledataView(
                name=d.name,
                sort_name=d.name,
                phone=d.phone,
                fax=d.fax,
                organization=d.org.name,
                org_id=d.org.id,
                building=d.bldg.name,
                bldg_id=d.bldg.id,
                room=d.room,
                from_table='departments'
            )

            record.save(doing_import=True)

class CombinedTeledataView(models.Model):
    alpha = models.NullBooleanField(default=True, null=True, blank=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    first_name = models.CharField(max_length=14, null=True, blank=True)
    last_name = models.CharField(max_length=25, null=True, blank=True)
    sort_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    fax = models.CharField(max_length=255, null=True, blank=True)
    postal = models.CharField(max_length=10, null=True, blank=True)
    job_position = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    dept_id = models.IntegerField(null=True, blank=True)
    organization = models.CharField(max_length=255, null=True, blank=True)
    org_id = models.IntegerField(null=True, blank=True)
    building = models.CharField(max_length=255, null=True, blank=True)
    bldg_id = models.IntegerField(null=True, blank=True)
    room = models.CharField(max_length=255, null=True, blank=True)
    from_table = models.CharField(max_length=255, null=False, blank=False)
    objects = CombinedTeledataViewManager()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def save(self, doing_import=False):
        """
        Prevent saving on the model unless the
        doing_import parameter is True
        """
        if doing_import:
            super(CombinedTeledataView, self).save()
        else:
            raise NotImplementedError(message="Saving is not possible on this method unless importing.")

    def delete(self, doing_import=False):
        """
        Prevent deleting on the model unless the
        doing_import parameter is True
        """
        if doing_import:
            super(CombinedTeledataView, self).delete()
        else:
            raise NotImplementedError(message="Deleting is not possible on this method unless importing.")

