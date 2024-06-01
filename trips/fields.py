from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class OrderField(models.PositiveIntegerField):
    """
    Custom Order field which defines the order of an object in a catalog.
    This class inherits from Django's PositiveIntegerField and adds the following
    specific functionalities

        1. Automatically assign an order value when no specific order is provided
        2. Order objects with respect to other fields.

    This field is generic in nature and can be used with any model whose objects need
    ordering with respect to each other.

    The `for_fields` parameter should be the parent model with respect to whom the order
    rank should be obeyed.
    """

    def __init__(self, for_fields=None, *args, **kwargs):
        self.for_fields = for_fields
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            # no current value
            try:
                qs = self.model.objects.all()

                if self.for_fields:
                    # filter by objects with the same field values
                    # for the fields in "for fields"
                    query = {
                        field: getattr(model_instance, field)
                        for field in self.for_fields
                    }
                    qs = qs.filter(**query)

                # get the order of the last item
                last_item = qs.latest(self.attname)
                value = last_item.order + 1

            except ObjectDoesNotExist:
                value = 0

            setattr(model_instance, self.attname, value)
            return value

        else:
            # order value already exists
            return super().pre_save(model_instance, add)
