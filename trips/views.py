from django.views.generic import TemplateView


class TripSearchView(TemplateView):
    template_name = "trips/trip_search.html"
