from django.core.management.base import BaseCommand, CommandError
from teledata.models import *
import settings
import logging

import urllib2
import logging
from django.utils import timezone
from collections import namedtuple

import MySQLdb

class Command(BaseCommand):
    conn = None
    help = 'Imports teledata from the shadow tables provided by IKM'

    last_updated  = timezone.now()
    bldg_created  = 0
    bldg_updated  = 0
    bldg_skipped  = 0
    bldg_error    = 0
    org_created   = 0
    org_updated   = 0
    org_skipped   = 0
    org_error     = 0
    org_deleted   = 0
    dept_created  = 0
    dept_updated  = 0
    dept_skipped  = 0
    dept_error    = 0
    dept_deleted  = 0
    staff_created = 0
    staff_updated = 0
    staff_skipped = 0
    staff_error   = 0
    staff_deleted = 0
    logger        = logging.getLogger(__name__)

    def add_arguments(self, parser):
        pass

    @property
    def connection_data(self):
        return settings.DATABASES['teledata']

    @property
    def bldg_query(self):
        return """
SELECT
    bldgnum,
    bldgname,
    bldgdesc,
    bldgabrev,
    Pkid
FROM
    ucfbldg;
        """

    @property
    def org_query(self):
        return """
SELECT
    orgid,
    name,
    BldgNum,
    Room,
    zip,
    phone,
    fax,
    comments,
    comments2,
    url,
    PkId
FROM
    organization;
        """

    @property
    def dept_query(self):
        return """
SELECT
    deptid,
    orgid,
    sort,
    name,
    BldgNumber,
    Room,
    phone,
    fax,
    comments,
    comments2,
    PkId
from
    department;
        """

    @property
    def staff_query(self):
        return """
SELECT
    ID,
    LAST,
    SUFFIX,
    TITLE,
    FIRST,
    MIDDLE,
    EMPID,
    deptid,
    POS,
    POSID,
    BldgNum,
    ROOM,
    PHONE,
    EMAIL,
    MACHINE,
    POSTAL,
    alpha,
    CellPhone,
    AltPhone,
    PkId
FROM
    individual;
        """

    @property
    def connection(self):
        if self.conn is None:
            self.conn = MySQLdb.connect(
                host=self.connection_data['HOST'],
                user=self.connection_data['USER'],
                passwd=self.connection_data['PASSWORD'],
                db=self.connection_data['NAME'],
                port=self.connection_data['PORT']
            )

        return self.conn

    def import_bldgs(self, data):
        for item in data:
            # Require name and abrev
            if item[1] is None or item[3] is None:
                self.bldg_skipped += 1
                continue

            try:
                existing = Building.objects.get(import_id=item[0])
                existing.name = item[1]
                existing.description = item[2]
                existing.abbr = item[3]

                try:
                    existing.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.bldg_error += 1

                self.bldg_updated += 1

            except Building.DoesNotExist:
                new = Building(
                    name=item[1],
                    description=item[2],
                    abbr=item[3],
                    import_id=item[0]
                )

                try:
                    new.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.bldg_error += 1

                self.bldg_created += 1

    def import_orgs(self, data):
        for item in data:
            # Require name
            if item[1] is None:
                self.org_skipped += 1
                continue

            try:
                existing = Organization.objects.get(import_id=item[0])
                existing.name = item[1]
                existing.room = item[3]
                existing.postal = item[4]
                existing.phone = item[5]
                existing.fax = item[6]
                existing.primary_comment = item[7]
                existing.secondary_comment = item[8]
                existing.url = item[9]
                existing.last_updated = self.last_updated
                existing.import_id = item[0]

                try:
                    existing.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.org_error += 1


                self.org_updated += 1

            except Organization.DoesNotExist:
                try:
                    bldg = Building.objects.get(import_id=item[2])
                except Building.DoesNotExist:
                    bldg = None

                new = Organization(
                    name = item[1],
                    bldg = bldg,
                    room = item[3],
                    postal = item[4],
                    phone = item[5],
                    fax = item[6],
                    primary_comment = item[7],
                    secondary_comment = item[8],
                    url = item[9],
                    last_updated = self.last_updated,
                    import_id = item[0]
                )

                try:
                    new.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.org_error += 1

                self.org_created += 1

    def import_depts(self, data):
        for item in data:
            # Require name
            if item[3] is None:
                self.dept_skipped += 1
                continue

            try:
                org = Organization.objects.get(import_id=item[1])
            except Organization.DoesNotExist:
                org = None

            try:
                bldg = Building.objects.get(import_id=item[4])
            except Building.DoesNotExist:
                bldg = None

            try:
                existing = Department.objects.get(import_id=item[0])
                existing.org = org
                existing.list_order = item[2]
                existing.name = item[3]
                existing.bldg = bldg
                existing.room = item[5]
                existing.phone = item[6]
                existing.fax = item[7]
                existing.primary_comment = item[8]
                existing.secondary_comment = item[9]
                existing.last_updated = self.last_updated

                try:
                    existing.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.dept_error += 1

                self.dept_updated += 1

            except Department.DoesNotExist:
                new = Department(
                    org=org,
                    list_order=item[2],
                    name=item[3],
                    bldg=bldg,
                    room=item[5],
                    phone=item[6],
                    fax=item[7],
                    primary_comment=item[8],
                    secondary_comment=item[9],
                    last_updated=self.last_updated,
                    import_id=item[0]
                )

                self.bldg_created += 1

                try:
                    new.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.dept_error += 1

    def import_staff(self, data):
        for item in data:
            if item[1] is None or item[4] is None:
                self.staff_skipped += 1
                continue

            try:
                dept = Department.objects.get(import_id=item[7])
            except Department.DoesNotExist:
                dept = None

            try:
                bldg = Building.objects.get(import_id=item[10])
            except Building.DoesNotExist:
                bldg = None

            if item[16] in [1, "1"]:
                alpha = True
            else:
                alpha = False

            if (item[13] is not None and
                item[14] is not None):
                email = item[13].lower() + item[14].lower()
                email_machine = item[14].lower()
            else:
                email = None
                email_machine = None

            try:
                existing = Staff.objects.get(import_id=item[0])
                existing.alpha = alpha
                existing.last_name = item[1]
                existing.suffix = item[2]
                existing.name_title = item[3]
                existing.first_name = item[4]
                existing.middle = item[5]
                existing.dept = dept
                existing.job_position = item[8]
                existing.bldg = bldg
                existing.room = item[11]
                existing.phone = item[12]
                existing.email = email
                existing.email_machine = email_machine
                existing.postal = item[15]
                existing.last_updated = self.last_updated
                existing.cellphone = item[17]

                try:
                    existing.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.staff_error += 1

                self.staff_updated += 1

            except Staff.DoesNotExist:
                new = Staff(
                    alpha=alpha,
                    last_name=item[1],
                    suffix=item[2],
                    name_title=item[3],
                    first_name=item[4],
                    middle=item[5],
                    dept=dept,
                    job_position=item[8],
                    bldg=bldg,
                    room=item[11],
                    phone=item[12],
                    email=email,
                    email_machine=email_machine,
                    postal=item[15],
                    last_updated=self.last_updated,
                    listed=True,
                    cellphone=item[17],
                    import_id=item[0]
                )

                try:
                    new.save()
                except Exception, e:
                    self.logger.error(str(e))
                    self.staff_error += 1

                self.staff_created += 1

    def delete_stale(self):
        stale_orgs  = Organization.objects.filter(last_updated__lt=self.last_updated)
        stale_depts = Department.objects.filter(last_updated__lt=self.last_updated)
        stale_staff = Staff.objects.filter(last_updated__lt=self.last_updated)

        self.org_deleted = stale_orgs.count()
        self.dept_deleted = stale_depts.count()
        self.staff_deleted = stale_staff.count()

        stale_orgs.delete()
        stale_depts.delete()
        stale_staff.delete()

    def print_stats(self):
        stats = """
Buildings
---------
Updated: {0}
Created: {1}
Skipped: {2}
Errors : {3}

Organizations
-------------
Updated: {4}
Created: {5}
Skipped: {6}
Errors : {7}
Deleted: {8}

Departments
-----------
Updated: {9}
Created: {10}
Skipped: {11}
Errors : {12}
Deleted: {13}

Staff
-----
Updated: {14}
Created: {15}
Skipped: {16}
Errors : {17}
Deleted: {18}
        """.format(
            self.bldg_updated,
            self.bldg_created,
            self.bldg_error,
            self.bldg_skipped,
            self.org_updated,
            self.org_created,
            self.org_skipped,
            self.org_error,
            self.org_deleted,
            self.dept_updated,
            self.dept_created,
            self.dept_skipped,
            self.dept_error,
            self.dept_deleted,
            self.staff_updated,
            self.staff_created,
            self.staff_skipped,
            self.staff_error,
            self.staff_deleted
        )

        print(stats)

    def handle(self, *args, **options):
        # Get the Building Data
        bldg_query = """

        """
        cursor = self.connection.cursor()

        # Get data and import buildings
        cursor.execute(self.bldg_query)
        bldg_data = cursor.fetchall()

        self.import_bldgs(bldg_data)

        # Get data and import organizations
        cursor.execute(self.org_query)
        org_data = cursor.fetchall()

        self.import_orgs(org_data)

        # Get data and import departments
        cursor.execute(self.dept_query)
        dept_data = cursor.fetchall()

        self.import_depts(dept_data)

        # Get data and import staff
        cursor.execute(self.staff_query)
        staff_data = cursor.fetchall()

        self.import_staff(staff_data)

        # Delete all stale data
        self.delete_stale()

        CombinedTeledata.objects.update_data()

        self.print_stats()

        print "All done!"

        self.connection.close()
