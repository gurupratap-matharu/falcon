from unittest.mock import patch

from django.test import SimpleTestCase

from payments.modo import fetch_token


# read this
# https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
@patch("payments.modo.requests")
class ModoTests(SimpleTestCase):

    def test_fetch_token(self, MockClass):
        token = fetch_token()
        print(f"got mock token: {token}")
        self.assertTrue(MockClass.post.called)
        self.assertTrue(MockClass.post().json.called)
