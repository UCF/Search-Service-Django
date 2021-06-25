import re
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.db.models import Value as V
from django.db.models.functions import StrIndex
from progress.bar import ChargingBar  # TODO

from org_units.models import *
from teledata.models import Organization as TeledataOrg
from programs.models import College
from teledata.models import Department as TeledataDept
from programs.models import Department as ProgramDept


class Command(BaseCommand):
    help = 'Assigns relationships across various apps for organizations and departments'

    teledata_orgs_processed = set()
    colleges_processed = set()
    units_created = set()
    units_updated = set()
    units_deleted_count = 0
    teledata_depts_processed = set()
    program_depts_processed = set()
    dept_data_skipped_count = 0

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.

        NOTE: order is important here! Particularly,
        in order for teledata and Program Departments to
        map properly, Colleges must be mapped first.
        """
        self.map_orgs_colleges()
        self.map_orgs_teledata()
        self.map_depts_programs()
        self.map_depts_teledata()
        self.consolidate_duplicate_units()
        self.delete_stale_units()
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
            'Amateur Radio Club-K4UCF': ['AMATEUR RADIO CLUB-K4UCF'],
            'Barnes and Noble Bookstore @ UCF': ['BARNES & NOBLE BOOKSTORE@ UCF'],
            'Burnett School of Biomedical Sciences': ['Biomedical Sciences', 'BIOMEDICAL SCIENCES, BURNETT SCHOOL OF'],
            'Center for Advanced Transportation Systems Simulation (CATSS)': ['Ctr. for Advanced Transportation Sys. Simulation', 'CATSS'],
            'Civil, Environmental, and Construction Engineering': ['Civil, Environ, & Constr Engr'],
            'College of Business': ['BUSINESS ADMINISTRATION, COLLEGE OF', 'College of Business Administration'],
            'College of Optics and Photonics': ['CREOL, THE COLLEGE OF OPTICS AND PHOTONICS', 'CREOL'],
            'Counselor Education and School Psychology': ['Counslr Educ & Schl Psychology'],
            'Dean\'s Office': ['Office of the Dean'],
            'Department of Finance, Dr. P. Phillips School of Real Estate': ['DEPARTMENT OF FINANCE/DR. P. PHILLIPS SCHOOL OF REAL ESTATE'],
            'Finance': ['Budget & Finance'],
            'Food Service and Lodging Management': ['Food Svcs & Lodging Management'],
            'Industrial Engineering and Management Systems': ['Industrial Engr & Mgmt Sys'],
            'Interdisciplinary Studies': ['Office of Interdisc Studies'],
            'Judaic Studies': ['JUDAIC STUDIES PROGRAM'],
            'Learning Institute for Elders (LIFE @ UCF)': ['LIFE', 'LEARNING INSTITUTE FOR ELDERS  (LIFE @ UCF)'],
            'Modern Languages and Literatures': ['Modern Languages', 'Modern Language & Literatures'],
            'National Center for Optics and Photonics Education, Waco, TX': ['OP-TEC Nat. Ctr.,Optics & Photonics Ed./Waco,TX'],
            'School of Communication Sciences and Disorders': ['Communication Sciences & Disorders Department'],
            'School of Kinesiology and Physical Therapy': ['Kinesiology&Phys Thpy, Schl of'],
            'School of Politics, Security, and International Affairs': ['Pol, Scty & Intl Afrs, Schl of'],
            'School of Teacher Education': ['Teacher Education 2, School'],
            'Tourism, Events and Attractions': ['Tourism Event and Attractions', 'Tourism, Events and Attraction', 'Tourism, Events, and Attractions'],
            'UCF Card Office': ['UCF CARD', 'UCF Card'],
            'Women\'s Studies': ['Womens Studies', 'WOMEN\'S STUDIES PROGRAM', 'Women\'s Studies Program']
        }

        # Basic replacements ARE case-sensitive! They are performed
        # *after* names are Capital-Cased.
        basic_replacements = {
            '\'': ['’'],
            'Academic': ['Acad.'],
            'Additional': ['Add.'],
            'Administration': ['Adm.', 'Admin.'],
            ' and ': [' & '],
            'Application': ['App.'],
            'AVP': ['Avp'],
            'Business ': ['Bus '],
            'Café': ['Cafe'],
            'Center': ['Ctr.'],
            'Children': ['Childern'],
            'Communication ': ['Comm '],
            'Counselor': ['Counslr'],
            'Department': ['Dept'],
            'Demonstration': ['Demo.'],
            'Educational ': ['Educ. ', 'Educ ', 'Ed '],
            'Engineering': ['Engr'],
            'Florida': ['Fla.'],
            'General': ['Gen.'],
            'Graduate ': ['Grad '],
            'Information': ['Inform.'],
            'Institute': ['Inst.'],
            'International': ['Intl'],
            'Leadership': ['Ldrshp'],
            'Management': ['Mgmt.', 'Mgmt'],
            'NanoScience': ['Nanoscience'],
            'Office': ['Ofc.'],
            'Programs': ['Prgms'],
            'Prop.': ['Prop.'],
            'Regional': ['Rgnl'],
            'Services': ['Svcs', 'Srvcs'],
            'School ': ['Schl '],
            'Sciences ': ['Sci '],
            'Technology': ['Tech.']
        }

        # These words should always be lowercase
        lowercase_replacements = [
            'and', 'of', 'for', 'in', 'at'
        ]

        # These words should always be uppercase/all-caps
        uppercase_replacements = [
            'AVP', 'CHAMPS', 'CREATE', 'FM', 'GTA', 'HRIS', 'IT',
            'LETTR', 'LINK', 'NASA', 'RESTORES', 'ROTC', 'STAT', 'TV',
            'TV/FM', 'UCF', 'WUCF',
        ]

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
        # capital case. This is not perfect but should work well
        # enough for the majority of use cases.
        if name.isupper():
            name_parts = name.split('(')
            for i, name_part in enumerate(name_parts):
                words = name_part.split(' ')
                if len(words) == 1 and name_part[-1] == ')':
                    # This part of the name is most likely an abbreviation
                    # enclosed in parentheses. Force it to be uppercase.
                    words[0] = words[0].upper()
                else:
                    for j, word in enumerate(words):
                        # word can be an empty string here; just ignore it
                        if not word:
                            continue

                        # if word ends in closing parentheses or a comma,
                        # temporarily remove it for the sake of manipulating
                        # the word
                        end_char = ''
                        if word[-1] in [')', ',']:
                            end_char = word[-1]
                            word = word[:-1]

                        if j == 0 and end_char == ')':
                            # This part of the name is most likely an
                            # abbreviation enclosed in parentheses.
                            # Force it to be uppercase.
                            words[j] = word.upper()
                        else:
                            if word.lower() in lowercase_replacements:
                                words[j] = word.lower()
                            elif word.upper() not in uppercase_replacements:
                                words[j] = word[0].upper() + word[1:].lower()
                            else:
                                words[j] = word.upper()

                        # If we removed an end character earlier,
                        # stick it back on:
                        if end_char:
                            words[j] = words[j] + end_char

                name_parts[i] = ' '.join(words)
            name = '('.join(name_parts)

            # Ensure that parts of a word divided by a dash or slash
            # have the 2nd portion's 1st character capitalized
            name = '-'.join([
                word[0].upper() + word[1:] for word in name.split('-')
            ])
            name = '/'.join([
                word[0].upper() + word[1:] for word in name.split('/')
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

        # Fix capitalization on names containing " The "
        name = name.replace(' The ', ' the ')

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

        # Force lowercase replacements on names not already
        # affected by logic above
        name = ' '.join([
            word.lower() if word.lower() in lowercase_replacements else word for word in name.split(' ')
        ])

        # Force uppercase replacements on names not already
        # affected by logic above
        name = ' '.join([
            word.upper() if word.upper() in uppercase_replacements else word for word in name.split(' ')
        ])

        # Again, trim whitespace from the start and end of the name,
        # and replace more than one instance of a single space "  ..." with
        # a single space
        name = name.strip()
        name = re.sub('\s+', ' ', name)

        print("{}\n".format(name))

        return name

    def get_unit_by_name(self, name, parent_unit=None):
        """
        Retrieves a Unit by its sanitized name.
        Handles incrementing of script created/updated flags.
        """
        unit_name_sanitized = self.sanitize_unit_name(name)
        if unit_name_sanitized:
            if parent_unit:
                # Relationships between Departments and Organizations
                # across Programs and Teledata are wildly inconsistent.
                # Assume that a Unit is the one we're looking for if we get a
                # name match, and `parent_unit` is present _somewhere_ up the
                # Unit parent relationship chain.
                possible_parent_units = parent_unit.get_all_relatives()

                # If the parent dept/org shares the same name as its child,
                # return the parent Unit
                if unit_name_sanitized == parent_unit.name:
                    unit = parent_unit
                    parent_unit = parent_unit.parent_unit
                    created = False
                elif len(possible_parent_units) > 0:
                    try:
                        # Try to get a single existing Unit match:
                        unit = Unit.objects.get(
                            name=unit_name_sanitized,
                            parent_unit__in=possible_parent_units
                        )
                        created = False
                    except Unit.DoesNotExist:
                        # Proceed with creating a new Unit with the
                        # original `parent_unit`.
                        unit = Unit(
                            name=unit_name_sanitized,
                            parent_unit=parent_unit
                        )
                        unit.save()
                        created = True
                    except Unit.MultipleObjectsReturned:
                        # There are multiple Units with this name that are
                        # assigned a parent in `possible_parent_units`, so we
                        # can't accurately determine which one is the "right"
                        # one to use. Skip.
                        self.dept_data_skipped_count += 1
                        return (None, None)
                else:
                    # Assume this Unit shouldn't have a parent.
                    unit, created = Unit.objects.get_or_create(
                        name=unit_name_sanitized,
                        parent_unit=None
                    )
            else:
                # Try to find a match for an Organization that belongs
                # to a College:
                try:
                    unit = Unit.objects.get(
                        name=unit_name_sanitized,
                        parent_unit__college__isnull=False
                    )
                    created = False
                except (Unit.DoesNotExist, Unit.MultipleObjectsReturned):
                    # This is probably an Organization or a College.
                    # Procced with getting/creating a Unit with no parent.
                    unit, created = Unit.objects.get_or_create(
                        name=unit_name_sanitized,
                        parent_unit=None
                    )

            if created:
                self.units_created.add(unit)
            elif unit not in self.units_created:
                self.units_updated.add(unit)

            return (unit, parent_unit)
        else:
            return (None, None)

    def map_orgs_colleges(self):
        """
        Gets or creates a Unit from corresponding
        College data, and maps the College to the Unit.
        """
        colleges = College.objects.all()
        self.colleges_processed = colleges

        for college in colleges:
            unit, parent_unit = self.get_unit_by_name(college.full_name)
            college.unit = unit
            college.save()

    def map_orgs_teledata(self):
        """
        Gets or creates a Unit from corresponding
        teledata, and maps the teledata to the Unit.
        """
        teledata_orgs = TeledataOrg.objects.annotate(college_index=StrIndex('name', V('college'))).order_by('-college_index')
        self.teledata_orgs_processed = teledata_orgs

        # Loop through all Teledata Organizations. Organizations that
        # look like they could align to a College should go first (see
        # `annotate()`/`order_by()` above)
        for teledata_org in teledata_orgs:
            # Try to extract a parent College's Unit from teledata meta;
            # use it as the parent Unit if available
            org_college_unit = self.get_college_unit_by_teledata_org(teledata_org)

            unit, parent_unit = self.get_unit_by_name(teledata_org.name, org_college_unit)
            teledata_org.unit = unit
            teledata_org.save()

            if unit is not None and parent_unit is not None:
                unit.parent_unit = parent_unit
                unit.save()

    def map_depts_programs(self):
        """
        Gets or creates a Unit from corresponding
        program data, and maps the program data to the Unit.
        """
        program_depts = ProgramDept.objects.all()
        self.program_depts_processed = program_depts

        for program_dept in program_depts:
            # Use a College Unit as the matchable parent Unit
            # for all Program Departments:
            colleges = College.objects.filter(program__departments=program_dept).distinct()
            if colleges.count() == 1:
                college_unit = colleges.first().unit
            else:
                college_unit = None

            unit, parent_unit = self.get_unit_by_name(program_dept.full_name, college_unit)
            program_dept.unit = unit
            program_dept.save()

            if unit is not None:
                unit.parent_unit = parent_unit
                unit.save()

    def map_depts_teledata(self):
        """
        Gets or creates a Unit from corresponding Department teledata,
        and maps the Department teledata to the Unit.
        """
        teledata_depts = TeledataDept.objects.all()
        self.teledata_depts_processed = teledata_depts

        for teledata_dept in teledata_depts:
            teledata_org_unit = teledata_dept.org.unit
            if teledata_dept.name == 'Main' or teledata_dept.name == 'Main Office':
                # A lot of redundant teledata gets saved in Departments
                # named "Main" or "Main Office". Consolidate them into their
                # parent early:
                unit = teledata_org_unit
                parent_unit = teledata_org_unit.parent_unit
            else:
                unit, parent_unit = self.get_unit_by_name(teledata_dept.name, teledata_org_unit)
            teledata_dept.unit = unit
            teledata_dept.save()

            if unit is not None:
                unit.parent_unit = parent_unit
                unit.save()

    def get_college_unit_by_teledata_org(self, teledata_org):
        """
        Sniffs through a Teledata Organization's metadata to determine
        what College Unit it should belong to.
        """
        college_unit = None

        secondary_comment = teledata_org.secondary_comment
        url = teledata_org.url
        college_units = Unit.objects.filter(college__isnull=False)

        if secondary_comment:
            # If there's something present in `secondary_comment`,
            # try to extract out a college name from the first line
            # in the comment to match against:
            secondary_comment_fl = secondary_comment.split("\n", 1)[0]
            secondary_comment_fl = secondary_comment_fl.replace('(', '').replace(')', '')
            secondary_comment_fl = self.sanitize_unit_name(secondary_comment_fl)
            college_unit = next((c for c in college_units if c.name == secondary_comment_fl), None)
        elif url:
            # As a fallback, try to see if `url` looks like a subdomain
            # of an existing College's teledata URL
            url = urlparse(url)
            url_domain = url.netloc.replace('www.', '')
            for c in college_units:
                try:
                    for org in c.teledata_organizations.all():
                        org_url = urlparse(org.url)
                        org_url_domain = org_url.netloc.replace('www.', '')
                        if org_url_domain in url_domain:
                            college_unit = c
                            break
                    if college_unit:
                        break
                except AttributeError:
                    continue

        return college_unit

    def consolidate_duplicate_units(self):
        """
        Attempts to consolidate Units with exactly 2 identical name matches.
        Considering the logic in this script, we cannot accurately determine
        dupes of more than two name matches, and can only make assumptions
        about Units when one of the two is missing a parent.
        """
        dupe_names = Unit.objects.values('name').annotate(name_count=Count('pk')).filter(name_count=2)
        for dupe_name in dupe_names:
            try:
                # The dupe without a parent must *not* have a College
                # assigned to it. Higher-level organizations can contain
                # a College.
                dupe_with_parent = Unit.objects.get(name=dupe_name['name'], parent_unit__isnull=False)
                dupe_without_parent = Unit.objects.get(name=dupe_name['name'], parent_unit__isnull=True, college__isnull=True)
            except (Unit.DoesNotExist, Unit.MultipleObjectsReturned):
                continue

            # Assume the dupe with a parent is the preferred Unit.
            # Update the dupe with a parent with values from the
            # orphan Unit:
            if dupe_without_parent.child_units:
                for child in dupe_without_parent.child_units.all():
                    child.parent_unit = dupe_with_parent
                    child.save()
            if dupe_without_parent.teledata_organizations:
                for org in dupe_without_parent.teledata_organizations.all():
                    org.unit = dupe_with_parent
                    org.save()
            if dupe_without_parent.teledata_departments:
                for teledata_dept in dupe_without_parent.teledata_departments.all():
                    teledata_dept.unit = dupe_with_parent
                    teledata_dept.save()
            if dupe_without_parent.program_departments:
                for program_dept in dupe_without_parent.program_departments.all():
                    program_dept.unit = dupe_with_parent
                    program_dept.save()

            # Finally, delete the dupe with no parent:
            if dupe_without_parent in self.units_created:
                self.units_created.remove(dupe_without_parent)
            elif dupe_without_parent in self.units_updated:
                self.units_updated.remove(dupe_without_parent)
            else:
                self.units_deleted_count += 1

            dupe_without_parent.delete()

    def delete_stale_units(self):
        """
        Deletes Units that no longer have any
        external ForeignKey relationships.
        """
        stale_units = Unit.objects.filter(
            parent_unit__isnull=True,
            child_units__isnull=True,
            teledata_departments__isnull=True,
            teledata_organizations__isnull=True,
            program_departments__isnull=True
        )
        self.units_deleted_count = len(stale_units)

        if len(stale_units):
            stale_units.delete()

    def print_stats(self):
        mapped_colleges = len(College.objects.filter(unit__isnull=False).distinct())
        mapped_teledata_orgs = len(TeledataOrg.objects.filter(unit__isnull=False))
        mapped_program_depts = len(ProgramDept.objects.filter(unit__isnull=False))
        mapped_teledata_depts = len(TeledataDept.objects.filter(unit__isnull=False))
        # TODO update to make either teledata_departments__isnull OR teledata_organizations__isnull check
        #fully_mapped_units = len(Unit.objects.filter(teledata_departments__isnull=False, teledata_organizations__isnull=False, program_data__isnull=False))

        stats = """
Colleges from Programs processed      : {}
Organizations from Teledata processed : {}
Departments from Programs processed   : {}
Departments from Teledata processed   : {}
Department data skipped               : {}

Units created                         : {}
Units updated                         : {}
Units deleted                         : {}

Colleges mapped to a Unit with teledata: {}/{} ({}%)
Organizations in Teledata with mapped Units: {}/{} ({}%)
Program Departments with mapped Units: {}/{} ({}%)
Departments in Teledata with mapped Units: {}/{} ({}%)
Units with mapped Program Departments *and* Teledata (that can have both): {}/{} ({}%)
Units with mapped Program Departments related to a Unit with a College: {}/{} ({}%)

        """.format(
            len(self.colleges_processed),
            len(self.teledata_orgs_processed),
            len(self.program_depts_processed),
            len(self.teledata_depts_processed),
            self.dept_data_skipped_count,

            len(self.units_created),
            len(self.units_updated),
            self.units_deleted_count,

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

            'TODO',
            'TODO',
            'TODO',

            'TODO',
            'TODO',
            'TODO',
        )

        self.stdout.write(stats)
