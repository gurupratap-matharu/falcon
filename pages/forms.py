import logging

from django import forms
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class FeedbackForm(forms.Form):
    subject = "Feedback Message"
    email = forms.EmailField(
        required=True,
        min_length=10,
        widget=forms.TextInput(attrs={"placeholder": "Email"}),
    )
    message = forms.CharField(
        min_length=20,
        max_length=1000,
        required=True,
        widget=forms.Textarea(
            attrs={
                "cols": 80,
                "rows": 5,
                "placeholder": "Send us your feedback or report an issue. Please provide as much info as possible. Thank you.",
            }
        ),
    )

    def send_mail(self):
        from_email = self.cleaned_data["email"]
        message = "Email: {email}\n\n{message}".format(**self.cleaned_data)

        logger.info("sending feedback...")
        send_mail(
            subject=self.subject,
            message=message,
            from_email=from_email,
            recipient_list=[settings.DEFAULT_TO_EMAIL],
            fail_silently=False,
        )


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        min_length=3,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Name"}),
    )
    email = forms.EmailField(
        required=True,
        min_length=10,
        widget=forms.TextInput(attrs={"placeholder": "Email"}),
    )
    subject = forms.CharField(
        max_length=100,
        min_length=3,
        widget=forms.TextInput(attrs={"placeholder": "Subject"}),
    )
    message = forms.CharField(
        min_length=20,
        max_length=600,
        required=True,
        widget=forms.Textarea(attrs={"cols": 80, "rows": 5, "placeholder": "Message"}),
    )

    def send_mail(self):

        subject = self.cleaned_data["subject"]
        from_email = self.cleaned_data["email"]
        message = "From: {name}\nEmail: {email}\n\n{message}".format(
            **self.cleaned_data
        )

        logger.info("sending contact form email...")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[settings.DEFAULT_TO_EMAIL],
            fail_silently=False,
        )
