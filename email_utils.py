"""
Email sending helpers for certificate delivery.
"""

from __future__ import annotations

import smtplib
import time
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

DEFAULT_SUBJECT = "Certificate of Participation"
DEFAULT_BODY = """Dear {name},

Thank you for your participation.

Please find your certificate attached to this email.

Regards,
Organizing Team
"""


def normalize_column_name(column: str) -> str:
    return column.strip().lower().replace("_", " ")


def find_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    normalized = {normalize_column_name(col): col for col in fieldnames}
    for candidate in candidates:
        match = normalized.get(normalize_column_name(candidate))
        if match:
            return match
    return None


def parse_participants(rows: list[dict], fieldnames: list[str]) -> tuple[list[dict], list[str]]:
    """
    Extract name and email from CSV rows.

    Returns (participants, errors).
    """
    name_col = find_column(
        fieldnames,
        ["name", "name of student", "student name", "participant name"],
    )
    email_col = find_column(
        fieldnames,
        ["email", "e-mail", "email address", "mail"],
    )

    errors = []
    if not name_col:
        errors.append("CSV must include a Name column.")
    if not email_col:
        errors.append("CSV must include an Email column.")
    if errors:
        return [], errors

    participants = []
    for index, row in enumerate(rows, start=2):
        name = str(row.get(name_col, "")).strip()
        email = str(row.get(email_col, "")).strip()

        if not name and not email:
            continue

        if not name:
            errors.append(f"Row {index}: missing name.")
            continue

        if not email or "@" not in email:
            errors.append(f"Row {index}: invalid or missing email for '{name}'.")
            continue

        participants.append({"name": name, "email": email.lower()})

    return participants, errors


def build_email(
    sender_email: str,
    recipient_name: str,
    recipient_email: str,
    certificate_png: bytes,
    certificate_filename: str,
    subject: str,
    body_template: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    plain_body = body_template.format(name=recipient_name)
    message.set_content(plain_body)

    html_body = plain_body.replace("\n", "<br>\n")
    message.add_alternative(
        f"<html><body><p>{html_body}</p></body></html>",
        subtype="html",
    )

    message.add_attachment(
        certificate_png,
        maintype="image",
        subtype="png",
        filename=certificate_filename,
    )
    return message


def send_certificates(
    sender_email: str,
    app_password: str,
    participants: list[dict],
    template_bytes: bytes,
    subject: str,
    body_template: str,
    delay_seconds: float,
    generate_certificate,
    progress_callback=None,
):
    """
    Send one certificate email per participant.

    Yields dict rows with status updates for the UI.
    """
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(sender_email, app_password)

    total = len(participants)

    try:
        for index, participant in enumerate(participants, start=1):
            name = participant["name"]
            email = participant["email"]
            safe_filename = f"{name.replace(' ', '_')}.png"

            row = {
                "name": name,
                "email": email,
                "status": "failed",
                "error": "",
            }

            try:
                certificate_png = generate_certificate(template_bytes, name)
                message = build_email(
                    sender_email,
                    name,
                    email,
                    certificate_png,
                    safe_filename,
                    subject,
                    body_template,
                )
                server.send_message(message)

                row["status"] = "sent"
                time.sleep(delay_seconds)

            except Exception as error:
                row["error"] = str(error)

            if progress_callback:
                progress_callback(index, total, row)

            yield row

    finally:
        server.quit()
