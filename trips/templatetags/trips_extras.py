import logging

from django import template

register = template.Library()


logger = logging.getLogger(__name__)


@register.simple_tag
def get_duration(trip, origin, destination):
    return trip.get_duration(origin, destination)


@register.simple_tag
def get_departure(trip, location):
    return trip.get_departure(location)


@register.simple_tag
def get_arrival(trip, location):
    return trip.get_arrival(location)


@register.simple_tag
def get_price(trip, origin, destination):
    return trip.get_price(origin, destination)
