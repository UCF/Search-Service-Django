from django.conf import settings

import re

class Utilities:
    def sanitize_unit_name(name):
        """
        Sanitizes and normalizes the name of an organization
        or department for consistency and to make cross-app
        string matching possible
        """
        full_name_replacements = settings.UNIT_NAME_FULL_REPLACEMENTS
        basic_replacements = settings.UNIT_NAME_PARTIAL_REPLACEMENTS
        lowercase_replacements = settings.UNIT_NAME_LOWERCASE_REPLACEMENTS
        uppercase_replacements = settings.UNIT_NAME_UPPERCASE_REPLACEMENTS

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

        return name
