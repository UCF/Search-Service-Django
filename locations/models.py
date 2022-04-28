# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.gis.db import models as gismodels
from s3_file_field import S3FileField


# Table Models

class CampusType(models.Model):
    '''
    A taxonomical designation for a Campus
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Campus(models.Model):
    '''
    A generalized area that _can_ contain Buildings, Parking, Locations and
    Points of Interest.

    Correspond to Site objects from Facilities
    (https://spaceadmin.provost.ucf.edu/sitelist.asp), but are not inclusive
    of all objects on that list.
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    site_id = models.CharField(max_length=20, null=True, blank=True)
    import_id = models.CharField(max_length=255, null=True, blank=True)
    campus_type = models.ForeignKey(CampusType, on_delete=models.SET_NULL, null=True, blank=True)
    photo = S3FileField(upload_to='locations', null=True, blank=True)
    profile_url = models.URLField(blank=True)
    point_coords = gismodels.PointField(blank=True)

    class Meta:
        verbose_name_plural = 'campuses'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Facility(models.Model):
    '''
    A physical structure or space on a Campus that is not a Parking Lot.

    Correspond to relevant Building objects from Teledata/Facilities
    (https://spaceadmin.provost.ucf.edu/buildinglist.asp)
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    building_id = models.CharField(max_length=255, blank=True)
    abbreviation = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    photo = S3FileField(upload_to='locations', null=True, blank=True)
    profile_url = models.URLField(blank=True)
    point_coords = gismodels.PointField(null=True, blank=True)
    poly_coords = gismodels.PolygonField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'facilities'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class ParkingLot(models.Model):
    '''
    A physical lot or garage where vehicles can be parked.

    Correspond to relevant Building objects from Teledata/Facilities
    (https://spaceadmin.provost.ucf.edu/buildinglist.asp)
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    building_id = models.CharField(max_length=255, blank=True)
    abbreviation = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    photo = S3FileField(upload_to='locations', null=True, blank=True)
    point_coords = gismodels.PointField(null=True, blank=True)
    poly_coords = gismodels.PolygonField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class ParkingPermitType(models.Model):
    '''
    A taxonomical designation for Parking Zones.

    Correspond to permits available through UCF Parking Services.
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    color = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class ParkingZone(models.Model):
    '''
    A designated space within a Parking Lot where certain
    permit types can park.

    Can have one or more Parking Permit Types assigned to it.
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    permit_types = models.ManyToManyField(ParkingPermitType, related_name='parking_zones')
    poly_coords = gismodels.PolygonField(null=True, blank=True)

    def __unicode__(self):
        return f"{self.name} ({self.parking_lot.name})"

    def __str__(self):
        return f"{self.name} ({self.parking_lot.name})"


class LocationType(models.Model):
    '''
    A taxonomical designation for a Location
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Location(models.Model):
    '''
    A designated area for a dining location,
    retail space, office, organization or department
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    import_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    photo = S3FileField(upload_to='locations', null=True, blank=True)
    location_type = models.ForeignKey(LocationType, on_delete=models.SET_NULL, null=True, blank=True)
    profile_url = models.URLField(blank=True)
    point_coords = gismodels.PointField(null=True, blank=True)
    poly_coords = gismodels.PolygonField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class PointType(models.Model):
    '''
    A taxonomical designation for a Point of Interest
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'point of interest type'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class PointOfInterest(models.Model):
    '''
    An arbitrary physical thing that does not fall under
    any of the other object types defined above
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    import_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    photo = S3FileField(upload_to='locations', null=True, blank=True)
    point_type = models.ForeignKey(PointType, on_delete=models.SET_NULL, null=True, blank=True)
    point_coords = gismodels.PointField(null=True, blank=True)
    poly_coords = gismodels.PolygonField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'points of interest'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class GroupType(models.Model):
    '''
    A taxonomical designation for a Group
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Group(models.Model):
    '''
    An arbitrary grouping of Facilities, Parking Lots,
    Locations, and/or Points of Interest.
    '''
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    group_type = models.ForeignKey(GroupType, on_delete=models.SET_NULL, null=True, blank=True)
    facilities = models.ManyToManyField(Facility, related_name='facility_groups', blank=True)
    parking_lots = models.ManyToManyField(ParkingLot, related_name='parking_lot_groups', blank=True)
    locations = models.ManyToManyField(Location, related_name='location_groups', blank=True)
    points_of_interest = models.ManyToManyField(PointOfInterest, related_name='point_groups', blank=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
