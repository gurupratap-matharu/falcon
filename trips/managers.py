import logging
from datetime import timedelta

from django.apps import apps
from django.db import models
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, Sum, When
from django.db.models.fields import FloatField, IntegerField
from django.db.models.fields.json import KT
from django.db.models.functions import Cast, Round
from django.utils import timezone

logger = logging.getLogger(__name__)


class LocationManager(models.Manager):
    def get_by_natural_key(self, abbr):
        return self.get(abbr=abbr)


class PastManager(models.Manager):
    """
    Trip Model manager to work with past trips.
    Specifically useful for generating statistics from them
    """

    def get_model(self, name=None):
        return apps.get_model("trips", name)

    def get_queryset(self):
        """Build stats only on past trips"""

        qs = super().get_queryset()
        return qs.filter(departure__lt=timezone.now())

    def kpis(self, company_slug=None, date=None):
        """
        Generate the KPI data for a company for a particular date.
        We need this only on past data perhaps only for yesterday's date or any
        arbitrary date to show on the company dashboard page.

        Key kpis are
            - Sales in $$$
            - Bookings i.e. tickets sold
            - Occupancy %
            - Num of trips done in a day
        """

        Seat = self.get_model("Seat")

        yesterday = (timezone.now() - timedelta(days=1)).date()
        date = date or yesterday

        logger.info("crunching kpis for %s %s..." % (company_slug, date))

        # TODO: Review: Any seat that is not available is considered as occupied
        total = Cast(Count("seats"), FloatField())
        occupied = Count("seats", filter=~Q(seats__seat_status=Seat.AVAILABLE))

        # Find occupancy as %
        occupancy = Cast(100 * Sum("occupied") / Sum("total"), IntegerField())

        # Find revenue = price * bookings
        revenue = Cast(F("price") * occupied, IntegerField())

        qs = self.get_queryset()
        qs = qs.filter(departure__date=date)
        qs = qs.filter(company__slug=company_slug) if company_slug else qs
        qs = qs.annotate(total=total, occupied=occupied, revenue=revenue)

        kpis = qs.aggregate(
            occupancy=occupancy,  # <- occupancy % on avg
            bookings=Sum("occupied"),  # <-- Num tickets sold
            sales=Sum("revenue"),  # <-- Sales in $$
            trips=Count("id"),  # <-- Num of trips done
        )

        return kpis

    def __repr__(self):
        return "I only show trips from the past 🔮"


class FutureManager(models.Manager):
    """
    Extra manager for Trip Model which shows only active trips

    A trip is active when
        - departure is in the future
        - status is set to Active
    """

    def get_model(self, name=None):
        return apps.get_model("trips", name)

    def get_queryset(self):
        logger.info("showing only future trips(⏰)...")

        qs = super().get_queryset()
        return qs.filter(departure__gt=timezone.now())

    def active(self):
        logger.info("showing only active trips(🌳)...")

        Trip = self.get_model("Trip")
        return self.filter(status=Trip.ACTIVE)

    def search(
        self,
        origin=None,
        destination=None,
        departure=None,
        company_slug: str = None,
        ordering=None,
    ):
        """
        Search only active future trips based on
            - origin
            - destination
            - departure date
        """

        Seat = self.get_model("Seat")
        Price = self.get_model("Price")

        origin_lookup = f"schedule__{origin.abbr}__order"
        destination_lookup = f"schedule__{destination.abbr}__order"

        origin_order = Cast(KT(origin_lookup), IntegerField())
        destination_order = Cast(KT(destination_lookup), IntegerField())

        # prices = Price.objects.filter(
        #     route=OuterRef("route_id"),
        #     origin=origin,
        #     destination=destination,
        #     category=OuterRef("category"),
        # )
        # price = Subquery(prices.values("amount"))

        logger.info(
            "searching from:%s to:%s on:%s company:%s"
            % (origin, destination, departure, company_slug)
        )

        qs = self.active()

        qs = qs.filter(departure__date=departure)
        qs = qs.filter(schedule__has_keys=[origin.abbr, destination.abbr])

        qs = qs.alias(origin_order=origin_order, destination_order=destination_order)
        qs = qs.filter(origin_order__lt=F("destination_order"))

        qs = qs.filter(company__slug=company_slug) if company_slug else qs

        availability = Count("seats", filter=Q(seats__seat_status=Seat.AVAILABLE))

        qs = qs.annotate(availability=availability)
        # qs = qs.annotate(price=price)

        qs = qs.select_related("company", "route", "origin", "destination")
        qs = qs.order_by(ordering) if ordering else qs

        return qs

    def for_company(self, company_slug=None, active=True):
        """
        Build the Queryset with relevant stats for only one company
        """

        Seat = self.get_model("Seat")

        logger.info("showing only trips for company(🚌):%s..." % company_slug)

        availability = Count("seats", filter=Q(seats__seat_status=Seat.AVAILABLE))
        occupied = Cast(
            Count("seats", filter=~Q(seats__seat_status=Seat.AVAILABLE)), FloatField()
        )
        total = Cast(Count("seats"), FloatField())

        occupancy = Case(
            When(total=0, then=0),
            default=Cast(100 * occupied / total, IntegerField()),
        )

        # Convert occupancy to % of nearest multiple of 5 for progress bars
        occupancy = 5 * Round(occupancy / 5)

        # Find revenue = price * occupied seats
        revenue = Cast(F("price"), FloatField()) * occupied
        revenue = Cast(revenue, IntegerField())

        qs = self.active() if active else self.get_queryset()
        qs = qs.filter(company__slug=company_slug)
        qs = qs.annotate(availability=availability, occupied=occupied, total=total)
        qs = qs.annotate(occupancy=occupancy)
        qs = qs.annotate(revenue=revenue)
        qs = qs.order_by("departure")
        qs = qs.select_related("company", "origin", "destination")

        return qs

    def __repr__(self):
        return "I only show trips from the future 🔮"
