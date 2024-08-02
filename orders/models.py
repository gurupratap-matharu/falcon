import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField

from .validators import validate_birth_date

logger = logging.getLogger(__name__)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    passengers = models.ManyToManyField("Passenger", related_name="orders")

    name = models.CharField(_("name"), max_length=50)
    email = models.EmailField(
        _("email"), help_text=_("We'll email the ticket to this email id.")
    )
    residence = CountryField(
        _("residence"),
        blank_label="(Country of residence)",
        help_text=_("This helps us to show you the best payment options."),
    )
    paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=250, blank=True)
    coupon = models.ForeignKey(
        "coupons.Coupon",
        related_name="orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        indexes = [
            models.Index(fields=["-created_on"]),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_total_cost_before_discount(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        if self.discount:
            total_cost = self.get_total_cost_before_discount()
            return total_cost * (self.discount / Decimal(100))

        return Decimal(0)

    def get_total_cost(self):
        """
        Calculate the final cost of the order with discount
        """

        total_cost = self.get_total_cost_before_discount()
        discount = self.get_discount()

        return total_cost - discount

    def get_total_cost_usd(self):
        """Calculate the order cost in USD"""
        # TODO: Remove the hardcoded value
        cost_usd = self.get_total_cost() / 150
        return round(
            cost_usd, 2
        )  # <-- Configure this to be automatically pulled via live exchange rate

    def confirm(self, payment_id=None):
        """
        - Mark an order as paid
        - Link a payment transaction id with the order instance
        - Mark all seats in each order item as Booked
        """

        if not payment_id:
            raise ValidationError(
                "Order: %(order)s cannot be confirmed without a payment_id!",
                params={"order": self},
                code="invalid",
            )

        passengers = self.passengers.all()

        for order_item in self.items.all():
            order_item.trip.book_seats_with_passengers(
                seat_numbers=order_item.seats, passengers=passengers
            )

        logger.info("marking order %s as paid...(💰)" % self)
        self.paid = True
        self.payment_id = payment_id
        self.save()

        return self

    def get_stripe_url(self):
        if not self.payment_id:
            return ""

        path = "/test/" if "_test_" in settings.STRIPE_SECRET_KEY else "/"

        return f"https://dashboard.stripe.com{path}payments/{self.payment_id}"

    def get_ticket_url(self):
        return reverse("orders:ticket_pdf", args=[str(self.id)])


class OrderItem(models.Model):
    """
    The intermediate `through` model between a Trip and an Order
    """

    order = models.ForeignKey("Order", related_name="items", on_delete=models.CASCADE)
    trip = models.ForeignKey(
        "trips.Trip", related_name="order_items", on_delete=models.SET_NULL, null=True
    )
    origin = models.ForeignKey(
        "trips.Location", related_name="+", on_delete=models.SET_NULL, null=True
    )
    destination = models.ForeignKey(
        "trips.Location", related_name="+", on_delete=models.SET_NULL, null=True
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    seats = models.CharField(max_length=20)
    quantity = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self):
        # We can make this better
        return f"OrderItem {self.id}"

    def get_cost(self):
        """
        Returns the cost of a single trip x num of passengers.
        """

        return self.price * self.quantity

    def get_checkin_url(self):
        return reverse(
            "companies:checkin",
            kwargs={
                "slug": self.trip.company.slug,
                "order_id": str(self.order.id),
                "orderitem_id": self.id,
            },
        )


class Passenger(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        (None, _("Identification")),
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
        (None, _("Gender")),
        ("F", _("Female")),
        ("M", _("Male")),
    ]

    document_type = models.CharField(
        _("document type"), choices=DOCUMENT_TYPE_CHOICES, max_length=10
    )  # Could this be a foreign key?
    document_number = models.CharField(
        _("document number"), max_length=50
    )  # How can we verify this?
    nationality = CountryField(_("nationality"), blank_label="(Nationality)")  # type: ignore
    first_name = models.CharField(_("first name"), max_length=50)
    last_name = models.CharField(_("last name"), max_length=50)
    gender = models.CharField(_("gender"), choices=GENDER_CHOICES, max_length=1)
    birth_date = models.DateField(_("birth date"), validators=[validate_birth_date])

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message=_(
            "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        ),
    )
    phone_number = models.CharField(
        _("phone number"), validators=[phone_regex], max_length=17
    )  # how to separate country code out?

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = _("passenger")
        verbose_name_plural = _("passengers")
        indexes = [
            models.Index(fields=["-created_on"]),
        ]

    def __str__(self):
        return f"{self.first_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
