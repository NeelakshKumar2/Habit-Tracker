"""Outgoing email. SMTP when configured; otherwise nothing leaves the machine."""
from __future__ import annotations

import smtplib
import threading
from email.message import EmailMessage

from flask import current_app


def _smtp_send(settings, to: str, subject: str, body: str, log) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.smtp_from, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            if settings.smtp_starttls:
                s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
    except Exception:
        log.exception("mail delivery failed")


def default_mailer(app):
    """Returns send(to, subject, body). SMTP runs in a thread so a slow mail server never blocks a request."""
    settings, log = app.extensions["grit"], app.logger

    def send(to: str, subject: str, body: str) -> None:
        if not settings.smtp_host:
            log.warning("email not sent: GRIT_SMTP_HOST is not set (to=%s subject=%s)", "***", subject)
            if settings.env != "production":
                log.info("DEV EMAIL to=%s\n%s", to, body)
            return
        threading.Thread(target=_smtp_send, args=(settings, to, subject, body, log), daemon=True).start()
    return send
