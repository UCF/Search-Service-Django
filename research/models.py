from django.db import models

from teledata.models import Staff

# Create your models here.
class Researcher(models.Model):
    orcid_id = models.CharField(max_length=19, unique=True, blank=False, null=False)
    teledata_record = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='researcher_records')

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
