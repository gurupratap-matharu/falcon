from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, tag
from django.urls import resolve, reverse

from users.factories import UserFactory
from users.forms import AccountDeleteForm
from users.views import AccountDeleteView

CustomUser = get_user_model()


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
