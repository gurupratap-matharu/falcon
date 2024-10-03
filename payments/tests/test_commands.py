from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from payments.models import ModoToken
from payments.tests.utils import mock_token

# Remember: patch the func where its used not where its defined


@patch("payments.management.commands.fetch_modo_token.fetch_token", mock_token)
class FetchModoTokenTests(TestCase):
    def test_command_output(self):
        self.assertFalse(ModoToken.objects.exists())

        out = StringIO()
        call_command("fetch_modo_token", stdout=out)
        self.assertIn("token fetch successful", out.getvalue())
        self.assertTrue(ModoToken.objects.exists())
