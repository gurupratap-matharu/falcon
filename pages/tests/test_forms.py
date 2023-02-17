import logging

from django.core import mail
from django.test import TestCase

from captcha.conf import settings as captcha_settings

from pages.forms import ContactForm, FeedbackForm

logger = logging.getLogger(__name__)


class FeedbackFormTests(TestCase):
    def setUp(self):
        captcha_settings.CAPTCHA_TEST_MODE = True
        self.field_required_msg = "This field is required."
        self.form_data = {
            "email": "guestuser@email.com",
            "message": "Hey I have been thinking about you a lot! Would you like to hang around during the weekend?",
            "captcha_0": "dummy",
            "captcha_1": "PASSED",
        }

    def test_feedback_form_is_valid_for_valid_data(self):
        form = FeedbackForm(data=self.form_data)

        self.assertTrue(form.is_valid())

    def test_form_email_field_label(self):
        form = FeedbackForm(data=self.form_data)
        label = form.fields["email"].label

        self.assertTrue(label is None or label == "email")

    def test_form_message_field_label(self):
        form = FeedbackForm(data=self.form_data)
        label = form.fields["message"].label

        self.assertTrue(label is None or label == "message")

    def test_feedback_form_sends_email_for_valid_data(self):

        form = FeedbackForm(data=self.form_data)

        self.assertTrue(form.is_valid())

        with self.assertLogs(logger="pages.forms", level="INFO") as cm:
            form.send_mail()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, FeedbackForm.subject)

        self.assertGreaterEqual(len(cm.output), 1)
        self.assertEqual(cm.output, ["INFO:pages.forms:sending feedback..."])

    def test_empty_feedback_form_raises_valid_errors(self):
        form = FeedbackForm({})
        self.assertEqual(form.errors["email"][0], self.field_required_msg)
        self.assertEqual(form.errors["message"][0], self.field_required_msg)

    def test_feedback_form_is_invalid_for_missing_email_field(self):
        self.form_data.pop("email")
        form = FeedbackForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_feedback_form_is_invalid_for_missing_message_field(self):
        self.form_data.pop("message")
        form = FeedbackForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_feedback_form_for_invalid_field_length_raises_valid_errors(self):
        invalid_data = {
            "email": "a@b.com",
            "message": "-",
        }

        form = FeedbackForm(data=invalid_data)

        self.assertEqual(
            form.errors["email"][0],
            "Ensure this value has at least 10 characters (it has 7).",
        )
        self.assertEqual(
            form.errors["message"][0],
            "Ensure this value has at least 20 characters (it has 1).",
        )


class ContactFormTests(TestCase):
    def setUp(self):
        captcha_settings.CAPTCHA_TEST_MODE = True
        self.field_required_msg = "This field is required."
        self.form_data = {
            "name": "Guest User",
            "email": "guestuser@email.com",
            "subject": "Just want to say hi!",
            "message": "Hey I have been thinking about you a lot! Would you like to hang around during the weekend?",
            "captcha_0": "dummy",
            "captcha_1": "PASSED",
        }

    def test_contact_form_is_valid_for_valid_data(self):
        form = ContactForm(data=self.form_data)

        self.assertTrue(form.is_valid())

    def test_form_name_field_label(self):
        form = ContactForm(data=self.form_data)
        label = form.fields["name"].label

        self.assertTrue(label is None or label == "name")

    def test_form_name_email_label(self):
        form = ContactForm(data=self.form_data)
        label = form.fields["email"].label

        self.assertTrue(label is None or label == "email")

    def test_form_name_subject_label(self):
        form = ContactForm(data=self.form_data)
        label = form.fields["subject"].label

        self.assertTrue(label is None or label == "subject")

    def test_form_name_message_label(self):
        form = ContactForm(data=self.form_data)
        label = form.fields["message"].label

        self.assertTrue(label is None or label == "message")

    def test_contact_form_sends_email_for_valid_data(self):
        form = ContactForm(data=self.form_data)
        self.assertTrue(form.is_valid())

        with self.assertLogs("pages.forms", level="INFO") as cm:
            form.send_mail()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, self.form_data["subject"])
        self.assertGreaterEqual(len(cm.output), 1)
        self.assertEqual(cm.output, ["INFO:pages.forms:sending contact form email..."])

    def test_empty_contact_form_raises_valid_errors(self):
        form = ContactForm({})
        self.assertEqual(form.errors["name"][0], self.field_required_msg)
        self.assertEqual(form.errors["email"][0], self.field_required_msg)
        self.assertEqual(form.errors["subject"][0], self.field_required_msg)
        self.assertEqual(form.errors["message"][0], self.field_required_msg)

    def test_contact_form_is_invalid_for_missing_email_field(self):
        self.form_data.pop("email")
        form = ContactForm(self.form_data)

        self.assertFalse(form.is_valid())

    def test_contact_form_is_invalid_for_missing_name_field(self):
        self.form_data.pop("name")
        form = ContactForm(self.form_data)

        self.assertFalse(form.is_valid())

    def test_contact_form_is_invalid_for_empty_subject(self):
        self.form_data.pop("subject")
        form = ContactForm(self.form_data)

        self.assertFalse(form.is_valid())

    def test_contact_form_is_invalid_for_empty_message(self):
        self.form_data.pop("message")
        form = ContactForm(self.form_data)

        self.assertFalse(form.is_valid())

    def test_contact_form_with_invalid_field_lengths_raises_valid_errors(self):
        invalid_data = {
            "name": "ab",
            "email": "a@b.com",
            "subject": "XX",
            "message": "-",
        }

        form = ContactForm(data=invalid_data)

        self.assertEqual(
            form.errors["name"][0],
            "Ensure this value has at least 3 characters (it has 2).",
        )
        self.assertEqual(
            form.errors["email"][0],
            "Ensure this value has at least 10 characters (it has 7).",
        )
        self.assertEqual(
            form.errors["subject"][0],
            "Ensure this value has at least 3 characters (it has 2).",
        )
        self.assertEqual(
            form.errors["message"][0],
            "Ensure this value has at least 20 characters (it has 1).",
        )
