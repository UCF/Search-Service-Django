from django.db import models

from teledata.models import Staff

# Create your models here.
class Researcher(models.Model):
    orcid_id = models.CharField(max_length=19, unique=True, blank=False, null=False)
    teledata_record = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='researcher_records')
