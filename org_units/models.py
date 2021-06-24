from django.db import models

# Create your models here.


class Unit(models.Model):
    """
    TODO
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

    def get_college(self):
        college = None

        try:
            college = self.college
        except Unit.college.RelatedObjectDoesNotExist:
            parent = self.parent_unit
            while parent:
                if parent.college:
                    college = parent.college
                    break
                else:
                    parent = parent.parent_unit

        return college

    def get_topmost_parent(self):
        topmost_parent = self.parent_unit

        if topmost_parent is None:
            topmost_parent = self
        else:
            while topmost_parent:
                next_parent = topmost_parent.parent_unit
                if next_parent:
                    topmost_parent = next_parent
                else:
                    break

        return topmost_parent

    def get_all_relatives(self, start_from=None):
        """
        Returns all Units in a tree of parent/child
        relationships.
        """
        topmost_unit = start_from if start_from is not None else self.get_topmost_parent()
        relatives = [topmost_unit]

        try:
            children = topmost_unit.child_units.all()
            for child in children:
                child_relatives = child.get_all_relatives(child)
                relatives.extend(child_relatives)
        except Unit.RelatedObjectDoesNotExist:
            pass

        return relatives
