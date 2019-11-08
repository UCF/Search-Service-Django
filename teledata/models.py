# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models
from django.db.models import F, When, Case, Value, Expression
from django_mysql.models import QuerySet, QuerySetMixin

logger = logging.getLogger(__name__)

class MatchAgainst(Expression):
    """
    Custom expression that generated a MATCH() AGAINST()
    expression for full text search on a mysql server.
    """
    template = 'MATCH(%(expressions)s) AGAINST(%(query)s)'

    def __init__(self, expressions, query, output_field):
        super(MatchAgainst, self).__init__(output_field=output_field)
        if len(expressions) < 1:
            raise ValueError('expressions must have at least 1 elements')
        for expression in expressions:
            if not hasattr(expression, 'resolve_expression'):
                raise TypeError('%r is not an Expression' % expression)

        self.expressions = expressions
        self.query = query

    def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
        c = self.copy()
        c.is_summary = summarize

        for pos, expression in enumerate(self.expressions):
            c.expressions[pos] = expression.resolve_expression(query, allow_joins, reuse, summarize, for_save)

        return c

    def as_sql(self, compiler, connection, template=None):
        sql_expressions, sql_params = [], []

        for expression in self.expressions:
            sql, params = compiler.compile(expression)
            sql_expressions.append(sql)
            sql_params.extend(params)

        q_sql, q_params = compiler.compile(self.query)
        params.append(q_params)

        template = template or self.template

        data = {
            'expressions': ','.join(sql_expressions),
            'query': q_sql
        }

        return template % data, params

    def get_source_expressions(self):
        return self.expressions

    def set_source_expressions(self, expressions):
        self.expressions = expressions

class Building(models.Model):
    objects = QuerySet.as_manager()

    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    abbr = models.CharField(max_length=255, null=True, blank=True)
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
        return self.name

    def __str__(self):
        return self.name

class CombinedTeledataManager(models.Manager, QuerySetMixin):
    """
    Custom manager that allows for special queries
    and update methods
    """
    def search(self, search_query):
        match_score = MatchAgainst(
            [
                F('first_name'),
                F('last_name')
            ],
            Value(search_query),
            models.DecimalField()
        )

        match_name_score = MatchAgainst(
            [
                F('name')
            ],
            Value(search_query),
            models.DecimalField()
        )

        full_name_score = Case(
            When(
                name=search_query,
                then=15
            ),
            default=0,
            output_field=models.DecimalField()
        )

        phone_score = Case(
            When(
                phone=search_query,
                then=15
            ),
            default=0,
            output_field=models.DecimalField()
        )

        email_score = Case(
            When(
                phone=search_query,
                then=15
            ),
            default=0,
            output_field=models.DecimalField()
        )

        first_name_score = Case(
            When(
                first_name=search_query,
                then=13
            ),
            default=0,
            output_field=models.DecimalField()
        )

        last_name_score = Case(
            When(
                last_name=search_query,
                then=13
            ),
            default=0,
            output_field=models.DecimalField()
        )

        name_sounds_score = Case(
            When(
                name__sounds_like=search_query,
                then=12
            ),
            default=0,
            output_field=models.DecimalField()
        )

        last_name_sounds_score = Case(
            When(
                last_name__sounds_like=search_query,
                then=8
            ),
            default=0,
            output_field=models.DecimalField()
        )

        first_name_sounds_score = Case(
            When(
                first_name__sounds_like=search_query,
                then=8
            ),
            default=0,
            output_field=models.DecimalField()
        )

        department_score = Case(
            When(
                department=search_query,
                then=3
            ),
            default=0,
            output_field=models.DecimalField()
        )

        organization_score = Case(
            When(
                organization=search_query,
                then=3
            ),
            default=0,
            output_field=models.DecimalField()
        )

        department_like_score = Case(
            When(
                department__icontains=search_query,
                then=2
            ),
            default=0,
            output_field=models.DecimalField()
        )

        organization_like_score=Case(
            When(
                organization__icontains=search_query,
                then=3
            ),
            default=0,
            output_field=models.DecimalField()
        )

        queryset = self.annotate(
            score=(
                match_score +
                match_name_score +
                full_name_score +
                phone_score +
                email_score +
                first_name_score +
                last_name_score +
                name_sounds_score +
                last_name_sounds_score +
                first_name_sounds_score +
                department_score +
                organization_score +
                department_like_score +
                organization_like_score
            )
        ).filter(
            score__gt=0
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
            record = CombinedTeledata(
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

            try:
                record.save(doing_import=True)
            except Exception, e:
                logger.error(str(e))

        for o in orgs:
            record = CombinedTeledata(
                name=o.name,
                sort_name=o.name,
                phone=o.phone,
                fax=o.fax,
                building=o.bldg.name,
                bldg_id=o.bldg.id,
                room=o.room,
                from_table='organizations'
            )

            try:
                record.save(doing_import=True)
            except Exception, e:
                logger.error(str(e))

        for d in depts:
            record = CombinedTeledata(
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

            try:
                record.save(doing_import=True)
            except Exception, e:
                logger.error(str(e))

class CombinedTeledata(models.Model):
    pkid = models.AutoField(primary_key=True)
    id = models.IntegerField(auto_created=False)
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
    objects = CombinedTeledataManager()

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
            super(CombinedTeledata, self).save()
        else:
            raise NotImplementedError(message="Saving is not possible on this method unless importing.")

    def delete(self, doing_import=False):
        """
        Prevent deleting on the model unless the
        doing_import parameter is True
        """
        if doing_import:
            super(CombinedTeledata, self).delete()
        else:
            raise NotImplementedError(message="Deleting is not possible on this method unless importing.")

