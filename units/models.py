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
            parent = self.parent_unit
            while parent:
                try:
                    college = parent.college
                    break
                except Unit.college.RelatedObjectDoesNotExist:
                    if parent != parent.parent_unit:
                        parent = parent.parent_unit
                    else:
                        parent = None

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
            parents.append(topmost_parent)
            if topmost_parent != topmost_parent.parent_unit:
                topmost_parent = topmost_parent.parent_unit
            else:
                topmost_parent = None

        return parents

