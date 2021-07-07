import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import StrIndex
from progress.bar import ChargingBar

from units.models import *
from teledata.models import Organization as TeledataOrg
from programs.models import College
from teledata.models import Department as TeledataDept
from programs.models import Department as ProgramDept


class Command(BaseCommand):
    help = 'Assigns relationships across various apps for organizations and departments'

    full_name_replacements = {}
    basic_replacements = {}
    lowercase_replacements = []
    uppercase_replacements = []
    teledata_orgs_processed = None
    colleges_processed = None
    teledata_depts_processed = None
    program_depts_processed = None
    data_skipped_count = 0
    consolidatable_unit_names = []
    units_created = set()
    mapping_progress_bar = None
    cleanup_progress_bar = None

    def handle(self, *args, **options):
        """
        Main entry function for the command.
        Execution logic handled here.
        """
        # Remove all existing Units before proceeding.
        # Unfortunately, the logic in this importer currently
        # is not consistent on imports against existing Units
        # vs a fresh db, so to have the most accurate data we can,
        # we have to start fresh with each run.
        Unit.objects.all().delete()

        # Perform mapping.
        # NOTE: order is important here! Particularly,
        # in order for teledata and Program Departments to
        # map properly, Colleges must be mapped first.
        self.full_name_replacements = settings.UNIT_NAME_FULL_REPLACEMENTS
        self.basic_replacements = settings.UNIT_NAME_PARTIAL_REPLACEMENTS
        self.lowercase_replacements = settings.UNIT_NAME_LOWERCASE_REPLACEMENTS
        self.uppercase_replacements = settings.UNIT_NAME_UPPERCASE_REPLACEMENTS

        self.colleges_processed = College.objects.all()
        # Teledata Organizations that look like they could align to a College
        # should be prioritized for processing, hence the ordering here:
        self.teledata_orgs_processed = TeledataOrg.objects.annotate(
            college_index=StrIndex('name', V('college'))).order_by('-college_index')
        self.program_depts_processed = ProgramDept.objects.all()
        self.teledata_depts_processed = TeledataDept.objects.all()

        self.mapping_progress_bar = ChargingBar(
            'Mapping data...',
            max=self.colleges_processed.count() +
            self.teledata_orgs_processed.count() +
            self.program_depts_processed.count() +
            self.teledata_depts_processed.count()
        )
        self.map_orgs_colleges()
        self.map_orgs_teledata()
        self.map_depts_programs()
        self.map_depts_teledata()

        # Consolidate duplicate Units as best as we can.
        self.consolidatable_unit_names = Unit.objects.values('name').annotate(name_count=Count('pk')).filter(name_count=2)
        self.cleanup_progress_bar = ChargingBar(
            'Cleaning up...',
            max=self.consolidatable_unit_names.count()
        )
        self.consolidate_duplicate_units()

        # Done.
        self.print_stats()

    def sanitize_unit_name(self, name):
        """
        Sanitizes and normalizes the name of an organization
        or department for consistency and to make cross-app
        string matching possible
        """
        # Trim whitespace from the start and end of the name
        name = name.strip()

        # Replace more than one instance of a single space "  ..." with
        # a single space
        name = re.sub('\s+', ' ', name)

        # Perform initial full-name replacements
        for replacement, replaceables in self.full_name_replacements.items():
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
                            if word.lower() in self.lowercase_replacements:
                                words[j] = word.lower()
                            elif word.upper() not in self.uppercase_replacements:
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
        for replacement, replaceables in self.basic_replacements.items():
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
            word.lower() if word.lower() in self.lowercase_replacements else word for word in name.split(' ')
        ])

        # Force uppercase replacements on names not already
        # affected by logic above
        name = ' '.join([
            word.upper() if word.upper() in self.uppercase_replacements else word for word in name.split(' ')
        ])

        # Again, trim whitespace from the start and end of the name,
        # and replace more than one instance of a single space "  ..." with
        # a single space
        name = name.strip()
        name = re.sub('\s+', ' ', name)

        return name

    def get_unit_by_name(self, name, parent_unit=None):
        """
        Retrieves a Unit by its sanitized name.
        Handles incrementing of script's created flags.
        """
        unit_name_sanitized = self.sanitize_unit_name(name)
        if not unit_name_sanitized:
            return (None, None)

        if parent_unit:
            # If the parent dept/org shares the same name as its child,
            # return the parent Unit.
            if unit_name_sanitized.lower() == parent_unit.name.lower():
                unit = parent_unit
                parent_unit = parent_unit.parent_unit
                created = False
            else:
                try:
                    # See if we can get a match with the sanitized name
                    # and parent Unit provided first:
                    unit = Unit.objects.get(
                        name=unit_name_sanitized,
                        parent_unit=parent_unit
                    )
                    created = False
                except Unit.DoesNotExist:
                    # Relationships between Departments and Organizations
                    # across Programs and Teledata are wildly inconsistent.
                    # If we couldn't get a match above, assume that a Unit is
                    # the one we're looking for if we get a name match, and
                    # `parent_unit` is present _somewhere_ in the Unit parent
                    # relationship chain.
                    possible_parent_units = parent_unit.get_all_parents()

                    # If the Unit does not appear to map to a school, and
                    # the parent Unit maps to a College, add all school
                    # Units under the College to the list of possible
                    # parent Units to match against.
                    # NOTE: if relevant school-mapped Units haven't yet been
                    # created/imported, this logic won't have any effect!
                    parent_has_college = False
                    try:
                        parent_has_college = True if parent_unit.college else False
                    except:
                        pass
                    if parent_has_college and not 'school of' in unit_name_sanitized.lower():
                        parent_schools = Unit.objects.filter(
                            parent_unit=parent_unit,
                            name__icontains='school of'
                        ).all()
                        possible_parent_units += list(parent_schools)

                    if len(possible_parent_units):
                        try:
                            # Try to get a single existing Unit match:
                            unit = Unit.objects.get(
                                name=unit_name_sanitized,
                                parent_unit__in=possible_parent_units
                            )
                            created = False
                        except Unit.DoesNotExist:
                            # We've tried finding an existing Unit with the
                            # provided `parent_unit` and all available,
                            # possible relative parent Units, but failed.
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
                            self.data_skipped_count += 1
                            return (None, None)
                    else:
                        # `parent_unit` is the only possible parent Unit we
                        # have to work with, so proceed with creating a
                        # new Unit:
                        unit = Unit(
                            name=unit_name_sanitized,
                            parent_unit=parent_unit
                        )
                        unit.save()
                        created = True
        else:
            # Try to find a single match for an existing Unit whose
            # immediate parent maps to a College:
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
                    parent_unit__isnull=True
                )

        if created:
            self.units_created.add(unit)

        return (unit, parent_unit)

    def map_orgs_colleges(self):
        """
        Gets or creates a Unit from corresponding
        College data, and maps the College to the Unit.
        """
        for college in self.colleges_processed:
            self.mapping_progress_bar.next()

            unit, parent_unit = self.get_unit_by_name(college.full_name)
            college.unit = unit
            college.save()

    def map_orgs_teledata(self):
        """
        Gets or creates a Unit from corresponding
        teledata, and maps the teledata to the Unit.
        """
        for teledata_org in self.teledata_orgs_processed:
            self.mapping_progress_bar.next()

            # Try to extract a parent College's Unit from teledata meta;
            # use it as the parent Unit if available
            org_college_unit = self.get_college_unit_by_teledata_org(teledata_org)

            unit, parent_unit = self.get_unit_by_name(teledata_org.name, org_college_unit)
            teledata_org.unit = unit
            teledata_org.save()

            if unit is not None:
                unit.parent_unit = parent_unit
                unit.save()

    def map_depts_programs(self):
        """
        Gets or creates a Unit from corresponding
        program data, and maps the program data to the Unit.
        """
        for program_dept in self.program_depts_processed:
            self.mapping_progress_bar.next()

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
        for teledata_dept in self.teledata_depts_processed:
            self.mapping_progress_bar.next()

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
            for c in college_units:
                try:
                    for org in c.teledata_organizations.all():
                        if org.url:
                            org_url = urlparse(org.url)
                            # The domain of the URL will be stored in
                            # `org_url.netloc` if urllib thinks it's
                            # not a relative URL; otherwise, the whole
                            # URL will get tossed into `org_url.path`:
                            org_url_domain = org_url.netloc.replace('www.', '') if org_url.netloc else org_url.path.split('/', 1)[0]
                            if org_url_domain and org_url_domain in url:
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
        for dupe_name in self.consolidatable_unit_names:
            self.cleanup_progress_bar.next()

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
            dupe_without_parent.delete()


    def print_stats(self):
        mapped_colleges = College.objects.filter(unit__isnull=False).distinct()
        mapped_teledata_orgs = TeledataOrg.objects.filter(unit__isnull=False)
        mapped_program_depts = ProgramDept.objects.filter(unit__isnull=False)
        mapped_teledata_depts = TeledataDept.objects.filter(unit__isnull=False)

        prog_depts_with_mapped_teledata = ProgramDept.objects.filter(
            Q(unit__teledata_departments__isnull=False) | Q(unit__teledata_organizations__isnull=False)
        ).distinct()
        prog_depts_with_mapped_college = [d for d in mapped_program_depts if d.unit.get_related_college() is not None]

        stats = """
Colleges from Programs processed      : {}
Organizations from Teledata processed : {}
Departments from Programs processed   : {}
Departments from Teledata processed   : {}
Department data skipped               : {}

Units created                         : {}

Colleges mapped to a Unit with teledata: {}/{} ({}%)
Organizations in Teledata with mapped Units: {}/{} ({}%)
Program Departments with mapped Units: {}/{} ({}%)
Departments in Teledata with mapped Units: {}/{} ({}%)
Program Departments mapped to a Unit with mapped Teledata: {}/{} ({}%)
Program Departments mapped to a Unit with a mapped College: {}/{} ({}%)

        """.format(
            len(self.colleges_processed),
            len(self.teledata_orgs_processed),
            len(self.program_depts_processed),
            len(self.teledata_depts_processed),
            self.data_skipped_count,

            len(self.units_created),

            len(mapped_colleges),
            len(self.colleges_processed),
            round((len(mapped_colleges) / len(self.colleges_processed)) * 100),

            len(mapped_teledata_orgs),
            len(self.teledata_orgs_processed),
            round((len(mapped_teledata_orgs) / len(self.teledata_orgs_processed)) * 100),

            len(mapped_program_depts),
            len(self.program_depts_processed),
            round((len(mapped_program_depts) / len(self.program_depts_processed)) * 100),

            len(mapped_teledata_depts),
            len(self.teledata_depts_processed),
            round((len(mapped_teledata_depts) / len(self.teledata_depts_processed)) * 100),

            len(prog_depts_with_mapped_teledata),
            len(self.program_depts_processed),
            round((len(prog_depts_with_mapped_teledata) / len(self.program_depts_processed)) * 100),

            len(prog_depts_with_mapped_college),
            len(self.program_depts_processed),
            round((len(prog_depts_with_mapped_college) / len(self.program_depts_processed)) * 100),
        )

        self.stdout.write(stats)
