from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import loader


def send_user_notification_email(
    recipient,
    subject,
    template_name,
    html_template_name,
    context=None,
):

    site = Site.objects.get_current()

    context = {
        "recipient": recipient,
        "site": site,
    } | (context or {})

    send_mail(
        f"[{site.name}] {subject}",
        loader.render_to_string(template_name, context),
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        html_message=loader.render_to_string(html_template_name, context),
    )
