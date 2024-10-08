from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

import factory

from trips.models import Location, Seat, Trip


class GroupFactory(factory.django.DjangoModelFactory):
    """Generic factory to create groups in a sequence"""

    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: "Group_{0}".format(n))


class OperatorGroupFactory(GroupFactory):
    """Our custom group that allows CRUD permissions on Trip | Location | Seat models"""

    name = "Operators"

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        # By default add Trip | Seat | Location CRUD permissions to operator group

        content_types = ContentType.objects.get_for_models(Trip, Location, Seat)
        perms = Permission.objects.filter(content_type__in=content_types.values())
        self.permissions.add(*perms)

        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.permissions.add(*extracted)  # type:ignore


class UserFactory(factory.django.DjangoModelFactory):
    """Public app users with normal privileges"""

    class Meta:
        model = get_user_model()
        django_get_or_create = ("email",)

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.LazyAttribute(
        lambda obj: "%s-%s" % (obj.first_name.lower(), obj.last_name.lower())
    )
    email = factory.LazyAttribute(lambda obj: "%s@email.com" % (obj.username))
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    location = factory.Faker("address")
    bio = factory.Faker("job")
    personal_website = factory.Faker("url")


class StaffuserFactory(UserFactory):
    """Internal users with staff privileges"""

    is_staff = True
    username = factory.Sequence(lambda n: "staffuser%d" % n)


class SuperuserFactory(StaffuserFactory):
    """This is me."""

    is_superuser = True
    username = factory.Sequence(lambda n: "superuser%d" % n)


class CompanyOwnerFactory(UserFactory):
    """
    A subset of our app users which are owners | staff of the companies they create.

    We need to add them to the `Operators` group so that they can do CRUD on
    trips | locations | seats models that they themselves create.
    """

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        # By default add CompanyOwner to the operator group
        operators = OperatorGroupFactory()
        self.groups.add(operators)

        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.groups.add(*extracted)  # type:ignore
