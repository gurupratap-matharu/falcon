import logging
from datetime import datetime

from django.apps import apps
from django.db import models
from django.db.models import Avg, Case, Count, F, Q, Sum, When
from django.db.models.fields import FloatField, IntegerField
from django.db.models.functions import Cast, Round
from django.shortcuts import get_object_or_404
from django.utils import timezone

logger = logging.getLogger(__name__)


class PastManager(models.Manager):
    """
    Trip Model manager to work with past trips.
    Specifically useful for generating statistics from them
    """

    def get_queryset(self):
        """Build stats only on past trips"""

        qs = super().get_queryset()
        return qs.filter(departure__lt=timezone.now())

    def kpis(self, company_slug=None):
        logger.info("crunching kpis...")
        Seat = apps.get_model(app_label="trips", model_name="Seat")

        # TODO: Review: Any seat that is not available is considered as occupied
        occupied = Count("seats", filter=~Q(seats__seat_status=Seat.AVAILABLE))

        # Find revenue = price * bookings
        revenue = Cast(F("price") * occupied, IntegerField())

        qs = self.get_queryset()
        qs = qs.filter(company__slug=company_slug) if company_slug else qs
        qs = qs.annotate(occupied=occupied, revenue=revenue)

        kpis = qs.aggregate(
            avg_occupancy=Avg("occupied"),
            bookings=Sum("occupied"),
            sales=Sum("revenue"),
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
        company_slug=None,
        ordering=None,
    ):
        """
        Search only active future trips based on
            - origin
            - destination
            - departure date
        """

        Location = self.get_model("Location")
        Seat = self.get_model("Seat")

        origin = get_object_or_404(Location, name=origin)
        destination = get_object_or_404(Location, name=destination)
        departure = datetime.strptime(departure, "%d-%m-%Y").date()

        logger.info(
            "searching from:%s to:%s on:%s company:%s"
            % (origin, destination, departure, company_slug)
        )

        qs = self.active()
        qs = qs.filter(origin=origin, destination=destination)
        qs = qs.filter(departure__date=departure)
        qs = qs.filter(company__slug=company_slug) if company_slug else qs

        availability = Count("seats", filter=Q(seats__seat_status=Seat.AVAILABLE))
        qs = qs.annotate(availability=availability)
        qs = qs.select_related("company", "origin", "destination")
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
