import datetime
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    passengers = models.ManyToManyField("Passenger", related_name="orders")

    name = models.CharField(max_length=50)
    email = models.EmailField(help_text=_("We'll email the ticket to this email id."))
    residence = CountryField(
        blank_label="(Country of residence)",
        help_text=_("This helps us to show you the best payment options."),
    )  # type: ignore
    paid = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_on"]
        indexes = [
            models.Index(fields=["-created_on"]),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_total_cost(self):
        """
        Calculate the cost of all (both?) the trips (forward + return)
        """

        return sum(item.get_cost() for item in self.items.all())  # type: ignore

    def get_total_cost_usd(self):
        """Calculate the order cost in USD"""

        cost_usd = self.get_total_cost() / 150
        return round(
            cost_usd, 2
        )  # <-- Configure this to be automatically pulled via live exchange rate


class OrderItem(models.Model):
    """
    The intermediate `through` model between a Trip and an Order
    """

    order = models.ForeignKey("Order", related_name="items", on_delete=models.CASCADE)
    trip = models.ForeignKey(
        "trips.Trip", related_name="order_items", on_delete=models.CASCADE
    )

    # Veer you might want to use the trip price directly as we would not want to use
    # a price saved in session. Session duration could be in days!
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Delete this?
    seats = models.CharField(max_length=20)
    quantity = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        # We can make this better
        return f"OrderItem {self.id}"

    def get_cost(self):
        """
        Returns the cost of a single trip x num of passengers.
        """

        return self.price * self.quantity


class Passenger(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        (None, "Identification"),
        ("DNI", "DNI"),
        ("PASSPORT", "PASSPORT"),
        ("CE", "CEDULA"),
        ("LE", "LE"),
        ("LC", "LC"),
        ("CUIT", "CUIT"),
        ("NIE", "NIE"),
        ("RG", "RG"),
        ("RNE", "RNE"),
        ("CPF", "CPF"),
        ("RUT", "RUT"),
        ("CURP", "CURP"),
        ("CNPJ", "CNPJ"),
    ]

    GENDER_CHOICES = [
        (None, "Gender"),
        ("F", "Female"),
        ("M", "Male"),
    ]

    document_type = models.CharField(
        choices=DOCUMENT_TYPE_CHOICES, max_length=10
    )  # Could this be a foreign key?
    document_number = models.CharField(max_length=50)  # How can we verify this?
    nationality = CountryField(blank_label="(Nationality)")  # type: ignore
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    birth_date = models.DateField()  # TODO: add validator for this

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message=_(
            "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17
    )  # how to separate country code out?

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_on"]
        indexes = [
            models.Index(fields=["-created_on"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="birth_date_not_in_future",
                check=Q(birth_date__lt=datetime.date.today()),
            )
        ]

    def __str__(self):
        return f"{self.first_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
