from django.db import models

# Create your models here.
class Unit(models.Model):
    """
    A generic 'unit' that represents a college,
    department, or organization
    """
    name = models.CharField(max_length=255, null=False, blank=False)
    parent_unit = models.ForeignKey('self',
                                    null=True,
                                    blank=True,
                                    related_name='child_units',
                                    on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def get_related_college(self):
        """
        Returns a College assigned to either the given Unit,
        or a College assigned to one of the Unit's parents.
        """
        college = None

        try:
            college = self.college
        except Unit.college.RelatedObjectDoesNotExist:
            all_parents = self.get_all_parents()
            for parent in all_parents:
                try:
                    college = parent.college
                    break
                except Unit.college.RelatedObjectDoesNotExist:
                    continue

        return college

    def get_topmost_parent(self):
        """
        Returns the uppermost parent Unit in the Unit's
        chain of parent relationships.  Will return the
        given Unit if it has no parent.
        """
        topmost_parent = self
        all_parents = self.get_all_parents()

        if len(all_parents):
            topmost_parent = all_parents[-1]

        return topmost_parent

    def get_all_parents(self):
        """
        Returns all parent Units related to the Unit,
        ordered by closest to furthest parent relationship
        (e.g. parent, grandparent, great-grandparent...)
        """
        parents = []
        topmost_parent = self.parent_unit

        while topmost_parent:
            if topmost_parent not in parents:
                parents.append(topmost_parent)
                topmost_parent = topmost_parent.parent_unit
            else:
                # We shouldn't ever get here if our data is sane,
                # but, just in case, ensure we don't wind up
                # in a recursive loop:
                break

        return parents


class Organization(models.Model):
    ext_org_id = models.CharField(max_length=10, null=False, blank=False)
    ext_org_name = models.CharField(max_length=255, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.ext_org_name

class College(models.Model):
    ext_college_name = models.CharField(max_length=255, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.ext_college_name

class Division(models.Model):
    ext_division_name = models.CharField(max_length=255, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.ext_division_name

class Department(models.Model):
    ext_department_id = models.CharField(max_length=10, null=False, blank=False)
    ext_department_name = models.CharField(max_length=255, null=False, blank=False)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.ext_department_name

class Employee(models.Model):
    ext_employee_id = models.CharField(max_length=7, null=False, blank=False)
    full_name = models.CharField(max_length=255, null=False, blank=False)
    first_name = models.CharField(max_length=255, null=False, blank=False)
    last_name = models.CharField(max_length=255, null=False, blank=False)
    prefix = models.CharField(max_length=10, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='employees')
    college = models.ForeignKey(College, null=True, blank=True, on_delete=models.CASCADE, related_name='employees')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employees')

    def __str__(self):
        return self.full_name
