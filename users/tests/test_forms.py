from django.test import SimpleTestCase

from users.forms import AccountDeleteForm


class AccountDeleteFormTests(SimpleTestCase):
    def setUp(self):
        self.field_required_msg = "This field is required."
        self.form_data = {"delete": True}

    def test_form_delete_field_label(self):
        form = AccountDeleteForm(data=self.form_data)
        label = form.fields["delete"].label

        self.assertTrue(label is None or label == "delete")

    def test_empty_account_delete_form_raises_valid_errors(self):
        form = AccountDeleteForm({})
        self.assertEqual(form.errors["delete"][0], self.field_required_msg)

    def test_contact_form_is_invalid_for_missing_delete_field(self):
        self.form_data.pop("delete")
        form = AccountDeleteForm(self.form_data)

        self.assertFalse(form.is_valid())
