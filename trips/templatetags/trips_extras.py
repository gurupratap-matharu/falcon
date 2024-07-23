import logging

from django import template

register = template.Library()


logger = logging.getLogger(__name__)


@register.simple_tag
def get_duration(trip, origin, destination):
    logger.info(
        "calculating duration for trip %s between %s - %s" % (trip, origin, destination)
    )
    return trip.get_duration(origin.abbr, destination.abbr)


@register.simple_tag
def get_departure(trip, location):
    logger.info("calculating departure for trip %s on location %s" % (trip, location))
    return trip.get_departure(location.abbr)


@register.simple_tag
def get_arrival(trip, location):
    logger.info("calculating arrival for trip %s on location %s" % (trip, location))
    return trip.get_arrival(location.abbr)
