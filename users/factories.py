import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
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
    is_staff = True
    username = factory.Sequence(lambda n: "staffuser%d" % n)


class SuperuserFactory(StaffuserFactory):
    is_superuser = True
    username = factory.Sequence(lambda n: "superuser%d" % n)
