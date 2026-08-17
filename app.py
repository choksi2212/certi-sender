import csv
from io import BytesIO, StringIO

import streamlit as st

from cert_utils import generate_certificate, get_font_path, preview_placement
from email_utils import DEFAULT_BODY, DEFAULT_SUBJECT, parse_participants, send_certificates


st.set_page_config(
    page_title="Certificate Mailer",
    page_icon="📧",
    layout="centered",
)

st.title("Certificate Mailer")
st.caption("Upload a template, upload a CSV, and send certificates automatically.")

with st.expander("How automatic name placement works"):
    st.markdown(
        """
        **You no longer need manual X/Y offsets.**

        1. The app scans your certificate template for a **horizontal underline**
           in the middle area (where names are usually written).
        2. If found, your participant name is **centered above that line**.
        3. If no line is found, the name is placed in a **default name band**
           (~46% from the top), which matches most certificate layouts.
        4. Long names automatically **shrink the font** until they fit within
           ~82% of the certificate width.

        Use **Preview placement** below to verify before sending.
        """
    )

st.subheader("1. Upload files")

col1, col2 = st.columns(2)

with col1:
    template_file = st.file_uploader(
        "Certificate template (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
    )

with col2:
    csv_file = st.file_uploader(
        "Participants CSV (Name + Email)",
        type=["csv"],
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
        st.success(f"Found **{len(participants)}** participants with valid emails.")

st.subheader("2. Email settings")

sender_email = st.text_input("Your Gmail address")
app_password = st.text_input("Gmail App Password", type="password")

subject = st.text_input("Email subject", value=DEFAULT_SUBJECT)
body_template = st.text_area(
    "Email message (use `{name}` for participant name)",
    value=DEFAULT_BODY,
    height=160,
)

delay_seconds = st.slider("Delay between emails (seconds)", 2, 10, 4)

st.subheader("3. Preview placement")

preview_name = st.text_input(
    "Sample name for preview",
    value="Alex Johnson",
)

if st.button("Preview placement", use_container_width=True):
    if not template_file:
        st.warning("Upload a certificate template first.")
    else:
        try:
            preview_png, info = preview_placement(
                template_file.getvalue(),
                preview_name,
            )
            st.image(preview_png, caption=f"Preview for: {preview_name}")

            if info["underline_detected"]:
                st.info(
                    "Underline detected automatically. "
                    f"Name placed above line at y={info['underline_y']}."
                )
            else:
                st.info(
                    "No underline detected. "
                    "Used default name band placement instead."
                )

            st.caption(
                f"Position: x={info['x']}, y={info['y']}, "
                f"font size={info['font_size']}"
            )
        except Exception as error:
            st.error(f"Preview failed: {error}")

st.subheader("4. Send certificates")

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
        status_box.write(
            f"Processing {current}/{total}: **{row['name']}** → {row['status']}"
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

    st.success(f"Done. Sent: {len(sent)} | Failed: {len(failed)}")

    if failed:
        st.error("Some emails failed:")
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
            "Download report CSV",
            data=report_buffer.getvalue(),
            file_name="certificate_send_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.divider()
st.caption(
    "Tip: create a Gmail App Password at "
    "https://myaccount.google.com/apppasswords "
    "(2-Step Verification must be enabled)."
)
