from django.db import models

from teledata.models import Staff

from pybtex.plugin import find_plugin
from pybtex.database import parse_string

APA = find_plugin('pybtex.style.formatting', 'apa')()
HTML = find_plugin('pybtex.backends', 'html')()

# Create your models here.
class Researcher(models.Model):
    orcid_id = models.CharField(max_length=19, unique=True, blank=False, null=False)
    teledata_record = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='researcher_records')
    biography = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '{0}, {1} - {2}'.format(
            self.teledata_record.last_name,
            self.teledata_record.first_name,
            self.orcid_id
        )

    def __str__(self):
        return '{0}, {1} - {2}'.format(
            self.teledata_record.last_name,
            self.teledata_record.first_name,
            self.orcid_id
        )

    @property
    def name_formatted_full_given(self):
        retval = f"{self.teledata_record.last_name}, {self.teledata_record.first_name}"
        retval += f" {self.teledata_record.middle[0]}." if self.teledata_record.middle not in (None, '') else ''
        return retval

    @property
    def name_formatted_initials(self):
        retval = f"{self.teledata_record.last_name}, {self.teledata_record.first_name[0]}."
        retval += f" {self.teledata_record.middle[0]}." if self.teledata_record.middle not in (None, '') else ''

        return retval

    @property
    def name_formatted_given_family(self):
        retval = self.teledata_record.first_name
        retval += f" {self.teledata_record.middle[0]}" if self.teledata_record.middle not in (None, '') else ''
        retval += f" {self.teledata_record.last_name}"

        return retval

class ResearcherEducation(models.Model):
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name='education')
    institution_name = models.CharField(max_length=255, blank=False, null=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    department_name = models.CharField(max_length=255, blank=True, null=True)
    role_name = models.CharField(max_length=255, null=False, blank=False)
    education_put_code = models.IntegerField(unique=True, null=False, blank=False,
        help_text='Primary key within ORCID education records. Uniquely identified the educational record within their system.')

    def __unicode__(self):
        return '{0} - {1}'.format(
            str(self.researcher),
            self.institution_name
        )

    def __str__(self):
        return '{0} - {1}'.format(
            str(self.researcher),
            self.institution_name
        )

    @property
    def education_dates(self) -> str:
        if not self.start_date and not self.end_date:
            return None

        if self.start_date and not self.end_date:
            return "{0} - Present".format(
                self.start_date.strftime("%m/%Y")
            )

        if not self.start_date and self.end_date:
            return self.end_date.strftime("%m/%Y")

        return "{0} - {1}".format(
            self.start_date.strftime("%m/%Y"),
            self.end_date.strftime("%m/%Y")
        )

class ResearchWork(models.Model):
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name='works')
    title = models.CharField(max_length=1000, blank=False, null=False)
    subtitle = models.CharField(max_length=1000, blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    publish_date = models.DateField(blank=False, null=False)
    bibtex_string = models.TextField(blank=True, null=True)
    work_type = models.CharField(max_length=255, blank=False, null=False)
    work_put_code = models.IntegerField(unique=True, blank=False, null=False,
        help_text='Primary key within ORCID work records. Uniquely identified the work within their system.')

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title

    @property
    def bibtex(self):
        if self.bibtex_string:
            try:
                return parse_string(self.bibtex_string, 'bibtex')
            except:
                pass

        return None

    @property
    def citation(self) -> str:
        if self.bibtex:
            try:
                return self.bib2html(self.bibtex)
            except:
                pass

        return None

    def bib2html(self, bibliography, exclude_fields=None):
        exclude_fields = exclude_fields or []
        if exclude_fields:
            bibliography = parse_string(bibliography.to_string('bibtex'), 'bibtex')
            for entry in bibliography.entries.values():
                for ef in exclude_fields:
                    if ef in entry.fields.__dict__['_dict']:
                        del entry.fields.__dict__['_dict'][ef]

        formattedBib = APA.format_bibliography(bibliography)
        return '<br>'.join(entry.text.render(HTML) for entry in formattedBib)
