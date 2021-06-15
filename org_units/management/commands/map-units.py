import re

from django.core.management.base import BaseCommand, CommandError
from org_units.models import *
from teledata.models import Organization as TeledataOrg
from programs.models import College
from teledata.models import Department as TeledataDept
from programs.models import Department as ProgramDept

from progress.bar import ChargingBar # TODO


class Command(BaseCommand):
    help = 'Assigns relationships across various apps for organizations and departments'

    teledata_orgs_processed = set()
    colleges_processed = set()
    org_units_created = set()
    org_units_updated = set()
    org_units_deleted_count = 0
    teledata_depts_processed = set()
    program_depts_processed = set()
    dept_units_created = set()
    dept_units_updated = set()
    dept_data_skipped_count = 0
    dept_units_deleted_count = 0

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.
        """
        self.map_orgs()
        self.map_depts()
        self.delete_stale_orgs()
        self.delete_stale_depts()
        self.assign_depts_to_orgs()
        self.print_stats()

    def sanitize_unit_name(self, name):
        """
        Sanitizes and normalizes the name of an organization
        or department for consistency and to make cross-app
        string matching possible
        """
        print(name)

        # Full name replacements ARE case-sensitive! They are performed
        # *before* names are Capital-Cased.
        full_name_replacements = {
            'Burnett School of Biomedical Sciences': ['Biomedical Sciences', 'BIOMEDICAL SCIENCES, BURNETT SCHOOL OF'],
            'Center for Advanced Transportation Systems Simulation (CATSS)': ['Ctr. for Advanced Transportation Sys. Simulation', 'CATSS'],
            'Civil, Environmental, and Construction Engineering': ['Civil, Environ, & Constr Engr'],
            'College of Optics and Photonics': ['CREOL, THE COLLEGE OF OPTICS AND PHOTONICS', 'CREOL'],
            'Counselor Education and School Psychology': ['Counslr Educ & Schl Psychology'],
            'Dean\'s Office': ['Office of the Dean'],
            'Department of Finance, Dr. P. Phillips School of Real Estate': ['DEPARTMENT OF FINANCE/DR. P. PHILLIPS SCHOOL OF REAL ESTATE'],
            'Food Service and Lodging Management': ['Food Svcs & Lodging Management'],
            'Industrial Engineering and Management Systems': ['Industrial Engr & Mgmt Sys'],
            'Interdisciplinary Studies': ['Office of Interdisc Studies'],
            'Judaic Studies': ['JUDAIC STUDIES PROGRAM'],
            'Modern Languages and Literatures': ['Modern Languages', 'Modern Language & Literatures'],
            'National Center for Optics and Photonics Education, Waco, TX': ['OP-TEC Nat. Ctr.,Optics & Photonics Ed./Waco,TX'],
            'School of Communication Sciences and Disorders': ['Communication Sciences & Disorders Department'],
            'School of Kinesiology and Physical Therapy': ['Kinesiology&Phys Thpy, Schl of'],
            'School of Politics, Security, and International Affairs': ['Pol, Scty & Intl Afrs, Schl of'],
            'School of Teacher Education': ['Teacher Education 2, School'],
            'Tourism, Events and Attractions': ['Tourism Event and Attractions', 'Tourism, Events and Attraction', 'Tourism, Events, and Attractions']
        }

        # Basic replacements ARE case-sensitive! They are performed
        # *after* names are Capital-Cased.
        basic_replacements = {
            'Academic': ['Acad.'],
            'Additional': ['Add.'],
            'Administration': ['Adm.', 'Admin.'],
            ' and ': [' & ', ' And '],
            'Application': ['App.'],
            'AVP': ['Avp'],
            'Business ': ['Bus ', 'Business Administration'],
            'Café': ['Cafe'],
            'Center': ['Ctr.'],
            'Children': ['Childern'],
            'Communication ': ['Comm '],
            'Counselor': ['Counslr'],
            'Department': ['Dept'],
            'Demonstration': ['Demo.'],
            'Educational ': ['Educ. ', 'Educ ', 'Ed '],
            'Engineering': ['Engr'],
            ' for ': [' For '],
            'Florida': ['Fla.'],
            'General': ['Gen.'],
            ' in ': [' In '],
            'Information Technology': ['Inform. Tech.'],
            'Institute': ['Inst.'],
            'International': ['Intl'],
            'Leadership': ['Ldrshp'],
            'Management': ['Mgmt.', 'Mgmt'],
            'NanoScience': ['Nanoscience'],
            ' of ': [' Of ', ' Of '],
            'Office': ['Ofc.'],
            'Prop.': ['Prop.'],
            'Regional': ['Rgnl'],
            'ROTC': ['Rotc'],
            'Services': ['Svcs', 'Srvcs'],
            'School ': ['Schl '],
            'Sciences ': ['Sci '],
            'Technology': ['Tech.'],
            'UCF': ['Ucf'],
        }

        # Trim whitespace from the start and end of the name
        name = name.strip()

        # Replace more than one instance of a single space "  ..." with
        # a single space
        name = re.sub('\s+', ' ', name)

        # Perform initial full-name replacements
        for replacement, replaceables in full_name_replacements.items():
            for replaceable in replaceables:
                if name == replaceable:
                    name = replacement

        # If the unit name is in all-caps, let's convert it to
        # capital case.  This is not perfect and will remove proper
        # all-caps on abbreviations not wrapped in parentheses, as
        # well as miss parentheses-wrapped content that are _not_
        # abbreviations.
        if name.isupper():
            name = ' '.join([
                word[0] + (word[1:] if word[0] == '(' or word[-1] == ')' else word[1:].lower()) for word in name.split(' ')
            ])

        # Perform basic string replacements
        for replacement, replaceables in basic_replacements.items():
            for replaceable in replaceables:
                name = name.replace(replaceable, replacement)

        # If "THE COLLEGE OF" or "UCF COLLEGE OF" is present anywhere
        # in the name, replace it just with "College of"
        name = re.sub('(UCF|the) college of', 'College of', name, flags=re.IGNORECASE)

        # If the unit name ends with "SCHOOL OF|FOR", "OFFICE OF|FOR",
        # or "CENTER FOR", split the name at the last present comma,
        # and flip the two portions.
        # \1: the (desired) end of the unit name
        # \2: the splitting comma
        # \3: an optional prefix to "school/office/center", e.g. "[nicholson] school of..."
        # \4: the captured "office/school/center" chunk
        # \5: " of" or " for"
        # \6: optional " the"
        # \7: optional content at the end of the name, wrapped in parentheses (usually an abbreviation)
        name = re.sub(
            r"^([\w\.\,\/\- ]+)(, )([\w\.\- ]+)?(office|school|center)( of| for)( the)?( \({1}[\w\.\,\/\- ]+\){1})?$",
            r"\3\4\5\6 \1\7",
            name,
            flags=re.IGNORECASE
        )

        # If the unit name ends with "COLLEGE OF", split the name at the last
        # present comma, and flip the two portions.  Works similarly to the
        # above logic for offices/schools/centers, but does not maintain
        # ending contents in parentheses (e.g. the college name abbreviation)
        # \1: the (desired) end of the unit name
        # \2: the splitting comma
        # \3: an optional prefix to "college", e.g. "[rosen] college of..."
        # \4: the captured "college of" chunk
        # \5: content at the end of the name, wrapped in parentheses (usually an abbreviation)
        name = re.sub(
            r"^([\w\.\,\/\- ]+)(, )([\w\.\- ]+)?(college of)( \({1}[\w\.\,\/\- ]+\){1})?$",
            r"\3\4 \1",
            name,
            flags=re.IGNORECASE
        )

        # If the unit name ends with ", school"
        # move it to the beginning of the unit name, and add " of"
        # \1: the (desired) end of the unit name
        # \2: the splitting comma
        # \3: the captured "school" chunk
        name = re.sub(
            r"^([\w\.\,\/\- ]+)(, )(school)$",
            r"School of \1",
            name,
            flags=re.IGNORECASE
        )

        # If ", UCF" is present at the end of the unit name,
        # remove it completely
        name = re.sub(', UCF$', '', name, flags=re.IGNORECASE)

        # If ", DIVISION OF" is present at the end of the unit name,
        # or "DIVISION OF" is present at the beginning of the unit name,
        # remove it completely
        name = re.sub(', division of$', '', name, flags=re.IGNORECASE)
        name = re.sub('^division of ', '', name, flags=re.IGNORECASE)

        # Remove instances of "department" and "department of" / ", department of"
        name = re.sub('(, )?department( of)?', '', name, flags=re.IGNORECASE)

        # If the unit name starts with "Dean's Suite|Office",
        # normalize the name to "Dean's Office"
        name = re.sub(
            r"^(Dean)(\'s)? (Office|Suite)([\w\.\,\/\- ]+)?$",
            "Dean's Office",
            name,
            flags=re.IGNORECASE
        )

        # If the unit name ends with "Dean's Suite|Office",
        # normalize the name to "Dean's Office"
        name = re.sub(
            r"^([\w\.\,\/\- ]+)?(Dean)(\'s)? (Office|Suite)$",
            "Dean's Office",
            name,
            flags=re.IGNORECASE
        )

        # Again, trim whitespace from the start and end of the name,
        # and replace more than one instance of a single space "  ..." with
        # a single space
        name = name.strip()
        name = re.sub('\s+', ' ', name)

        print("{}\n".format(name))

        return name

    def get_org_by_name(self, name):
        """
        Retrieves an Organization by its sanitized name.
        Handles incrementing of script created/updated flags.
        """
        org_name_sanitized = self.sanitize_unit_name(name)
        if org_name_sanitized:
            org_unit, created = OrganizationUnit.objects.get_or_create(
                name=org_name_sanitized
            )
            if created:
                self.org_units_created.add(org_unit)
            elif org_unit not in self.org_units_created:
                self.org_units_updated.add(org_unit)

            return org_unit
        else:
            return None

    def get_dept_by_name(self, name, organization_unit=None):
        """
        Retrieves a DepartmentUnit by its sanitized name.
        Handles incrementing of script created/updated flags.
        """
        dept_name_sanitized = self.sanitize_unit_name(name)
        if dept_name_sanitized:
            # If this is a Department from Teledata whose name matches
            # its Organization's name exactly, try to find an existing
            # DepartmentUnit whose OrganizationUnit maps to a College,
            # and use it instead.
            if organization_unit and organization_unit.name == dept_name_sanitized:
                try:
                    dept_unit = DepartmentUnit.objects.get(name=dept_name_sanitized, organization_unit__college__isnull=False)
                    organization_unit = dept_unit.organization_unit
                    created = False
                except (DepartmentUnit.DoesNotExist, DepartmentUnit.MultipleObjectsReturned):
                    self.dept_data_skipped_count += 1
                    return (None, None)
            else:
                dept_unit, created = DepartmentUnit.objects.get_or_create(
                    name=dept_name_sanitized,
                    organization_unit=organization_unit
                )

            if created:
                self.dept_units_created.add(dept_unit)
            elif dept_unit not in self.dept_units_created:
                self.dept_units_updated.add(dept_unit)

            return (dept_unit, organization_unit)
        else:
            return (None, None)

    def map_orgs(self):
        """
        Performs mapping for all Organization-related data

        NOTE: We assume that relationships for departments
        and organizations defined in the Programs app should
        be prioritized over relationships defined in Teledata.
        Therefore, *Colleges must be processed first!*
        """
        self.map_orgs_colleges()
        self.map_orgs_teledata()

    def map_orgs_teledata(self):
        """
        Gets or creates an OrganizationUnit from corresponding
        teledata, and maps the teledata to the OrganizationUnit.
        """
        teledata_orgs = TeledataOrg.objects.all()
        self.teledata_orgs_processed = teledata_orgs

        for teledata_org in teledata_orgs:
            org_unit = self.get_org_by_name(teledata_org.name)
            teledata_org.organization_unit = org_unit
            teledata_org.save()

    def map_orgs_colleges(self):
        """
        Gets or creates an OrganizationUnit from corresponding
        College data, and maps the College to the OrganizationUnit.
        """
        colleges = College.objects.all()
        self.colleges_processed = colleges

        for college in colleges:
            org_unit = self.get_org_by_name(college.full_name)
            college.organization_unit = org_unit
            college.save()

    def map_depts(self):
        """
        Performs mapping for all Department-related data.

        NOTE: We assume that relationships for departments
        and organizations defined in the Programs app should
        be prioritized over relationships defined in Teledata.
        Therefore, *Program data must be processed first!*
        """
        self.map_depts_programs()
        self.map_depts_teledata()

    def map_depts_teledata(self):
        """
        Gets or creates a DepartmentUnit from corresponding
        teledata, and maps the teledata to the DepartmentUnit.
        """
        teledata_depts = TeledataDept.objects.all()
        self.teledata_depts_processed = teledata_depts

        for teledata_dept in teledata_depts:
            teledata_org_unit = teledata_dept.org.organization_unit
            dept_unit, org_unit = self.get_dept_by_name(teledata_dept.name, teledata_org_unit)
            teledata_dept.department_unit = dept_unit
            teledata_dept.save()

            if dept_unit is not None:
                dept_unit.organization_unit = org_unit
                dept_unit.save()

    def map_depts_programs(self):
        """
        Gets or creates a DepartmentUnit from corresponding
        program data, and maps the program data to the DepartmentUnit.
        """
        program_depts = ProgramDept.objects.all()
        self.program_depts_processed = program_depts

        for program_dept in program_depts:
            colleges = College.objects.filter(program__departments=program_dept).distinct()
            if colleges.count() == 1:
                college = colleges.first().organization_unit
            else:
                college = None

            dept_unit, org_unit = self.get_dept_by_name(program_dept.full_name, college)
            program_dept.department_unit = dept_unit
            program_dept.save()

            if dept_unit is not None:
                dept_unit.organization_unit = org_unit
                dept_unit.save()

    def delete_stale_orgs(self):
        """
        Deletes OrganizationUnits that no longer have any
        external ForeignKey relationships.
        """
        stale_orgs = OrganizationUnit.objects.filter(
            teledata__isnull=True,
            college__isnull=True
        )
        self.org_units_deleted_count = len(stale_orgs)

        if len(stale_orgs):
            stale_orgs.delete()

    def delete_stale_depts(self):
        """
        Deletes DepartmentUnits that no longer have any
        external ForeignKey relationships.
        """
        stale_depts = DepartmentUnit.objects.filter(
            teledata__isnull=True,
            program_data__isnull=True
        )
        self.dept_units_deleted_count = len(stale_depts)

        if len(stale_depts):
            stale_depts.delete()

    def assign_depts_to_orgs(self):
        """
        TODO
        Assigns ForeignKey relationships from DepartmentUnits to
        OrganizationUnits, based on inferred teledata and program data.
        """
        return

    def print_stats(self):
        mapped_colleges = len(College.objects.filter(organization_unit__isnull=False, organization_unit__teledata__isnull=False).distinct())
        mapped_teledata_orgs = len(TeledataOrg.objects.filter(organization_unit__isnull=False))

        mapped_program_depts = len(ProgramDept.objects.filter(department_unit__isnull=False))
        mapped_teledata_depts = len(TeledataDept.objects.filter(department_unit__isnull=False))
        fully_mapped_dept_units = len(DepartmentUnit.objects.filter(teledata__isnull=False, program_data__isnull=False))

        dept_units_with_college_prog_data = len(DepartmentUnit.objects.filter(organization_unit__college__isnull=False, program_data__isnull=False))

        stats = """
Organizations from Teledata processed : {}
Colleges from Programs processed      : {}
OrganizationUnits created             : {}
OrganizationUnits updated             : {}
OrganizationUnits deleted             : {}
Departments from Teledata processed   : {}
Departments from Programs processed   : {}
DepartmentUnits created               : {}
DepartmentUnits updated               : {}
Department data skipped               : {}
DepartmentUnits deleted               : {}

Colleges with mapped OrganizationUnits *and* matched teledata: {}/{} ({}%)
Organizations in Teledata with mapped OrganizationUnits: {}/{} ({}%)
Program Departments with mapped DepartmentUnits: {}/{} ({}%)
Departments in Teledata with mapped DepartmentUnits: {}/{} ({}%)
DepartmentUnits with mapped Program Departments *and* Teledata (that can have both): {}/{} ({}%)
DepartmentUnits with mapped OrganizationUnits tied to a College: {}/{} ({}%)

        """.format(
            len(self.teledata_orgs_processed),
            len(self.colleges_processed),
            len(self.org_units_created),
            len(self.org_units_updated),
            self.org_units_deleted_count,
            len(self.teledata_depts_processed),
            len(self.program_depts_processed),
            len(self.dept_units_created),
            len(self.dept_units_updated),
            self.dept_data_skipped_count,
            self.dept_units_deleted_count,
            mapped_colleges,
            len(self.colleges_processed),
            round((mapped_colleges / len(self.colleges_processed)) * 100),
            mapped_teledata_orgs,
            len(self.teledata_orgs_processed),
            round((mapped_teledata_orgs / len(self.teledata_orgs_processed)) * 100),
            mapped_program_depts,
            len(self.program_depts_processed),
            round((mapped_program_depts / len(self.program_depts_processed)) * 100),
            mapped_teledata_depts,
            len(self.teledata_depts_processed),
            round((mapped_teledata_depts / len(self.teledata_depts_processed)) * 100),
            fully_mapped_dept_units,
            len(self.program_depts_processed),
            round((fully_mapped_dept_units / len(self.program_depts_processed)) * 100),
            dept_units_with_college_prog_data,
            len(self.program_depts_processed),
            round((dept_units_with_college_prog_data / len(self.program_depts_processed)) * 100),
        )

        self.stdout.write(stats)
