from django.contrib.auth import get_user_model
from django.test import TestCase

from users.factories import SuperuserFactory, UserFactory

CustomUser = get_user_model()


class CustomUserTests(TestCase):
    def test_create_normal_user(self):
        user = UserFactory()
        user_from_db = CustomUser.objects.first()

        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(user.username, user_from_db.username)
        self.assertEqual(user.email, user_from_db.email)

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = SuperuserFactory()
        superuser_from_db = CustomUser.objects.first()

        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(superuser.username, superuser_from_db.username)
        self.assertEqual(superuser.email, superuser_from_db.email)

        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
