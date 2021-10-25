from django.db import models

from teledata.models import Staff

# Create your models here.
class Researcher(models.Model):
    orcid_id = models.CharField(max_length=19, unique=False, blank=True, null=True)
    aa_person_id = models.IntegerField(null=True, blank=True)
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
    def name_formatted_title(self):
        title = self.teledata_record.name_title.strip()

        retval = f"{title} " if title== 'Dr.' else ''
        retval += f"{self.teledata_record.first_name} {self.teledata_record.last_name}"

        return retval

    @property
    def name_formatted_no_title(self):
        return f"{self.teledata_record.first_name} {self.teledata_record.last_name}"

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
    researchers = models.ManyToManyField(Researcher, related_name='works')

    @property
    def simple_citation_html(self):
        return ""

    def __str__(self):
        return self.citation

class Article(ResearchWork):
    aa_article_id = models.IntegerField(null=False, blank=False)
    article_title = models.CharField(max_length=1024, null=False, blank=False)
    journal_name = models.CharField(max_length=512, null=False, blank=False)
    article_year = models.IntegerField(null=False, blank=False)
    journal_volume = models.CharField(max_length=50, null=True, blank=True)
    journal_issue = models.CharField(max_length=50, null=True, blank=True)
    first_page = models.CharField(max_length=26, null=True, blank=True)
    last_page = models.CharField(max_length=26, null=True, blank=True)

    def __str__(self):
        return self.article_title

    @property
    def simple_citation_html(self):
        vol_issue = ''

        if self.journal_volume:
            vol_issue += self.journal_volume

        if self.journal_issue:
            vol_issue += f'({self.journal_issue})'

        pages = []
        if self.first_page:
            pages.append(self.first_page)
        if self.last_page:
            pages.append(self.last_page)

        pages = '-'.join(pages)

        retval = f'&ldquo;{self.article_title}&rdquo;, <em>{self.journal_name}</em>'

        if vol_issue:
            retval += f', Vol. {vol_issue}'

        if pages:
            retval += f', {pages}'

        if self.article_year:
            retval += f', {self.article_year}'

        return retval


class Book(ResearchWork):
    aa_book_id = models.IntegerField(null=False, blank=False)
    isbn = models.CharField(max_length=16, null=False, blank=False)
    book_title = models.CharField(max_length=320, null=False, blank=False)
    bisac = models.CharField(max_length=50, null=True, blank=True)
    publisher_name = models.CharField(max_length=40, null=True, blank=True)
    publish_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.book_title

    @property
    def simple_citation_html(self):
        return f'<em>{self.book_title}</em>, {self.publish_date.year}'

class BookChapter(ResearchWork):
    aa_book_id = models.IntegerField(null=False, blank=False)
    isbn = models.CharField(max_length=16, null=False, blank=False)
    book_title = models.CharField(max_length=320, null=False, blank=False)
    chapter_title = models.CharField(max_length=320, null=False, blank=False)
    bisac = models.CharField(max_length=50, null=True, blank=True)
    publisher_name = models.CharField(max_length=40, null=True, blank=True)
    publish_year = models.IntegerField(null=True, blank=True)
    publish_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.book_title}: {self.chapter_title}'

    @property
    def simple_citation_html(self):
        return f'&ldquo;{self.chapter_title}&rdquo;, <em>{self.book_title}</em>, {self.publish_year}'

class ConferenceProceeding(ResearchWork):
    aa_article_id = models.IntegerField(null=False, blank=False)
    proceeding_title = models.CharField(max_length=1024, null=False, blank=False)
    journal_name = models.CharField(max_length=512, null=False, blank=False)
    article_year = models.IntegerField(null=True, blank=True)
    journal_volume = models.CharField(max_length=50, null=True, blank=True)
    journal_issue = models.CharField(max_length=50, null=True, blank=True)
    first_page = models.CharField(max_length=26, null=True, blank=True)
    last_page = models.CharField(max_length=26, null=True, blank=True)

    def __str_(self):
        return self.proceeding_title

    @property
    def simple_citation_html(self):
        return f'&ldquo;{self.proceeding_title}&rdquo;, {self.journal_name}, {self.article_year}'

class Grant(ResearchWork):
    aa_grant_id = models.IntegerField(null=False, blank=False)
    agency_name = models.CharField(max_length=64, null=False, blank=False)
    grant_name = models.CharField(max_length=256, null=False, blank=False)
    duration_years = models.FloatField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    full_name = models.CharField(max_length=64, null=True, blank=True)
    total_dollars = models.IntegerField(null=False, blank=False)
    is_research = models.BooleanField(null=False, blank=False)
    principle_investigator = models.BooleanField(null=False, blank=False)

    def __str__(self):
        return self.grant_name

    @property
    def simple_citation_html(self):
        dates = []
        if self.start_date:
            dates.append(self.start_date.strftime('%m/%Y'))
        if self.end_date:
            dates.append(self.end_date.strftime('%m/%Y'))

        return f'<em>{self.grant_name}</em>, {self.agency_name}, {" - ".join(dates)}'


class HonorificAward(ResearchWork):
    aa_award_id = models.IntegerField(null=False, blank=False)
    governing_society_name = models.CharField(max_length=1024, null=False, blank=False)
    award_name = models.CharField(max_length=255, null=False, blank=False)
    award_received_name = models.CharField(max_length=128, null=False, blank=False)
    award_received_year = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.award_name

    @property
    def simple_citation_html(self):
        return f'<em>{self.award_name}</em>, {self.governing_society_name}, {self.award_received_year}'

class Patent(ResearchWork):
    patent_id = models.CharField(max_length=10, null=False, blank=False)
    patent_title = models.CharField(max_length=1024, null=False, blank=True)
    patent_type = models.CharField(max_length=40, null=False, blank=False)
    patent_kind = models.CharField(max_length=3, null=False, blank=False)
    patent_date = models.DateField(null=False, blank=False)
    country = models.CharField(max_length=2, null=False, blank=False)
    claims = models.IntegerField(null=False, blank=False)
    abstract = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.patent_title

    @property
    def simple_citation_html(self):
        return f'<em>{self.patent_title}</em>, {self.patent_type}, {self.patent_date.year}'

class ClinicalTrial(ResearchWork):
    nct_id = models.CharField(max_length=16, null=False, blank=False)
    title = models.CharField(max_length=2048, null=False, blank=False)
    start_date = models.DateField(null=False, blank=False)
    completion_date = models.DateField(null=True, blank=True)
    study_type = models.CharField(max_length=64, null=False, blank=False)
    sponsor = models.CharField(max_length=256, null=False, blank=False)
    allocation = models.CharField(max_length=32, null=True, blank=True)
    phase = models.CharField(max_length=32, null=True, blank=True)
    recruitment_status = models.CharField(max_length=32, null=True, blank=True)
    investigators = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def simple_citation_html(self):
        pass

