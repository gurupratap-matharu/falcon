from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, tag
from django.urls import resolve, reverse

from users.factories import UserFactory
from users.forms import AccountDeleteForm, ProfileEditForm
from users.views import AccountDeleteView, AccountSettingsView, ProfilePageView

CustomUser = get_user_model()


class ProfilePageTests(TestCase):
    """Test suite to verify profile page works"""

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("users:profile")

    def test_profile_page_view_redirects_for_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_profile_page_view_works_for_logged_in_user(self):
        self.client.force_login(self.user)  # type:ignore

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "users/profile.html")
        self.assertContains(response, "Profile")
        self.assertContains(response, self.user.username)  # type:ignore
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_profile_page_resolve_profilepageview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, ProfilePageView.as_view().__name__)


class ProfileEditTests(TestCase):
    """Test suite to verify profile editing works"""

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("users:settings")
        self.valid_data = {
            "first_name": "Inderpal Singh",
            "last_name": "Matharu",
            "bio": "My great father in heavens",
            "location": "Heavens",
            "personal_website": "https://inderpal.com",
        }

    def test_profile_edit_view_redirects_for_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_profile_edit_view_works_for_logged_in_user(self):
        self.client.force_login(self.user)  # type:ignore

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "users/profile_edit.html")
        self.assertContains(response, "Edit Profile")
        self.assertContains(response, "First name")
        self.assertContains(response, "Last name")
        self.assertContains(response, "Bio")
        self.assertContains(response, "Location")
        self.assertContains(response, "Personal website")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_profile_edit_resolves_profileeditview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, AccountSettingsView.as_view().__name__)

    def test_profile_edit_view_renders_profile_edit_form(self):
        self.client.force_login(self.user)  # type: ignore

        response = self.client.get(self.url)
        form = response.context["form"]

        self.assertIsInstance(form, ProfileEditForm)

    def test_profile_edit_view_works_on_successful_post(self):
        self.client.force_login(self.user)  # type:ignore

        response = self.client.post(self.url, data=self.valid_data)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], reverse("users:profile"))

        # Check that a confirmation message is included in the response
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), AccountSettingsView.success_message)

        # Check that profile is updated successfully
        user = CustomUser.objects.first()
        self.assertEqual(user.first_name, self.valid_data["first_name"])
        self.assertEqual(user.last_name, self.valid_data["last_name"])
        self.assertEqual(user.bio, self.valid_data["bio"])
        self.assertEqual(user.location, self.valid_data["location"])
        self.assertEqual(user.personal_website, self.valid_data["personal_website"])


@tag("delete")
class AccountDeleteTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("users:delete")
        self.valid_data = {"delete": True}

    def test_account_delete_view_redirects_for_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_account_delete_view_works_for_logged_in_user(self):
        self.client.force_login(self.user)  # type: ignore

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "users/account_delete.html")
        self.assertContains(response, "Delete")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_account_delete_page_url_resolves_accountdeleteview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, AccountDeleteView.as_view().__name__)

    def test_account_delete_view_renders_accountdeleteform(self):
        self.client.force_login(self.user)  # type: ignore

        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertIsInstance(form, AccountDeleteForm)

    @tag("delete", "important")
    def test_account_delete_view_deletes_user_on_successful_post(self):
        self.client.force_login(self.user)  # type: ignore
        response = self.client.post(self.url, data=self.valid_data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], reverse("pages:home"))

        # Check that a confirmation message is included in the response
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), AccountDeleteView.success_message)

        # Check that the user count is zero
        self.assertEqual(len(CustomUser.objects.all()), 0)

    @tag("messages")
    def test_account_delete_view_sends_valid_message_after_successul_deletion(self):
        self.client.force_login(self.user)  # type: ignore
        response = self.client.post(self.url, data=self.valid_data)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), AccountDeleteView.success_message)
