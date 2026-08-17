import csv
from io import StringIO

import streamlit as st

from cert_utils import generate_certificate, get_font_path, preview_certificate
from email_utils import DEFAULT_BODY, DEFAULT_SUBJECT, parse_participants, send_certificates
from ui.styles import PREMIUM_CSS, render_hero, section_card


st.set_page_config(
    page_title="Certi Sender",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
render_hero()

participants = []
csv_errors = []

section_card(
    "Step 01",
    "Upload your files",
    "Add your certificate template and the participant list to get started.",
    "delay-1",
)

upload_col1, upload_col2 = st.columns(2, gap="large")

with upload_col1:
    template_file = st.file_uploader(
        "Certificate template",
        type=["png", "jpg", "jpeg"],
        help="PNG or JPG template without participant names filled in.",
    )

with upload_col2:
    csv_file = st.file_uploader(
        "Participants CSV",
        type=["csv"],
        help="CSV must include participant names and email addresses.",
    )

if csv_file:
    csv_text = csv_file.getvalue().decode("utf-8-sig")
    reader = csv.DictReader(StringIO(csv_text))
    fieldnames = reader.fieldnames or []
    rows = list(reader)
    participants, csv_errors = parse_participants(rows, fieldnames)

    if csv_errors:
        for error in csv_errors:
            st.error(error)
    else:
        st.markdown(
            f'<div class="stat-pill">✓ {len(participants)} participants ready to receive certificates</div>',
            unsafe_allow_html=True,
        )

section_card(
    "Step 02",
    "Delivery settings",
    "Connect your Gmail account and customize the message your recipients will receive.",
    "delay-2",
)

settings_col1, settings_col2 = st.columns(2, gap="large")

with settings_col1:
    sender_email = st.text_input("Sender Gmail address")
    app_password = st.text_input("Gmail App Password", type="password")
    subject = st.text_input("Email subject", value=DEFAULT_SUBJECT)

with settings_col2:
    body_template = st.text_area(
        "Email message",
        value=DEFAULT_BODY,
        height=180,
        help="Use {name} to personalize each email.",
    )
    delay_seconds = st.slider("Delay between emails (seconds)", 2, 10, 4)

section_card(
    "Step 03",
    "Preview",
    "Check how one certificate looks before sending the full batch.",
    "delay-3",
)

preview_col1, preview_col2 = st.columns([1, 1.2], gap="large")

with preview_col1:
    preview_name = st.text_input("Sample participant name", value="Alex Johnson")
    preview_clicked = st.button("Generate preview", use_container_width=True)

with preview_col2:
    if preview_clicked:
        if not template_file:
            st.warning("Upload a certificate template first.")
        else:
            try:
                preview_png = preview_certificate(
                    template_file.getvalue(),
                    preview_name,
                )
                st.image(preview_png, use_container_width=True)
                st.caption(f"Preview for {preview_name}")
            except Exception as error:
                st.error(f"Preview failed: {error}")

section_card(
    "Step 04",
    "Send certificates",
    "Launch delivery when everything looks perfect.",
    "delay-4",
)

if st.button("Send all certificates", type="primary", use_container_width=True):
    if not template_file:
        st.error("Upload a certificate template.")
        st.stop()

    if not csv_file:
        st.error("Upload a participants CSV.")
        st.stop()

    if csv_errors:
        st.error("Fix CSV errors before sending.")
        st.stop()

    if not sender_email or not app_password:
        st.error("Enter your Gmail address and app password.")
        st.stop()

    if "{name}" not in body_template:
        st.warning("Your email body does not include `{name}`.")

    template_bytes = template_file.getvalue()
    font_path = get_font_path()

    progress_bar = st.progress(0.0)
    status_box = st.empty()
    results = []

    def update_progress(current, total, row):
        progress_bar.progress(current / total)
        status_box.markdown(
            f"**Sending {current}/{total}** · {row['name']} · `{row['status']}`"
        )

    try:
        for result in send_certificates(
            sender_email=sender_email.strip(),
            app_password=app_password,
            participants=participants,
            template_bytes=template_bytes,
            subject=subject.strip(),
            body_template=body_template,
            delay_seconds=float(delay_seconds),
            generate_certificate=lambda tb, name: generate_certificate(
                tb, name, font_path=font_path
            ),
            progress_callback=update_progress,
        ):
            results.append(result)

    except Exception as error:
        st.error(f"Could not connect or login to Gmail: {error}")
        st.stop()

    sent = [row for row in results if row["status"] == "sent"]
    failed = [row for row in results if row["status"] != "sent"]

    st.success(f"Delivery complete · Sent: {len(sent)} · Failed: {len(failed)}")

    if failed:
        st.error("Some emails could not be delivered:")
        for row in failed:
            st.write(f"- {row['name']} ({row['email']}): {row['error']}")

    if results:
        report_buffer = StringIO()
        writer = csv.DictWriter(
            report_buffer,
            fieldnames=["name", "email", "status", "error"],
        )
        writer.writeheader()
        writer.writerows(results)

        st.download_button(
            "Download delivery report",
            data=report_buffer.getvalue(),
            file_name="certificate_send_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown(
    """
    <div class="footer-note">
        Use a Gmail App Password for secure delivery.
        Credentials are never stored and only used during your active session.
    </div>
    """,
    unsafe_allow_html=True,
)
