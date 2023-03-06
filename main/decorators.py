from django.db import connection, reset_queries

from trips.models import Trip


def database_debug(func):
    """
    Decorator to count and print the queries for any function
    Veer this is very useful to find out n+1 problem in our queries.

    See this example

    @database_debug
    def check_query_performance():
        trips = Trip.objects.all()

        for trip in trips:
            # call all foreign keys...
            print(trip.company, trip.origin, trip.destination)

    """

    def inner_func(*args, **kwargs):
        reset_queries()
        results = func()

        query_info = connection.queries
        queries = ["{}\n".format(query["sql"]) for query in query_info]

        print("#" * 80)
        print(f"Function: {func.__name__} | Query count:{len(query_info)}")
        print("#" * 80)
        print("\n\nQueries: \n\n{}".format("\n".join(queries)))

        return results

    return inner_func


@database_debug
def check_query_performance():
    """This unoptimized query results in n+1 database hits!"""

    trips = Trip.objects.all()

    for trip in trips:
        # call all foreign keys...
        print(trip.company, trip.origin, trip.destination)  # Hits the database


@database_debug
def check_query_performance_with_select_related():
    """This optimized query results in only one database hit."""

    trips = Trip.objects.select_related("company", "origin", "destination").all()

    for trip in trips:
        # call all foreign keys...
        print(trip.company, trip.origin, trip.destination)  # no db hits
