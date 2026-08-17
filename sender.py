import csv
import os
import re
import time
import smtplib
import getpass
from email.message import EmailMessage


# ============================================================
# CONFIGURATION
# ============================================================

CSV_FILE = "Attendance_CONCEIT 2.0 16.02.2026 - Sheet1.csv"

CERTIFICATE_FOLDER = "Certi"

SENT_FILE = "sent.csv"
FAILED_FILE = "failed.csv"

EMAIL_DOMAIN = "@mbit.edu.in"

# IMPORTANT:
# Keep this TRUE for your first test.
# Change to FALSE only after checking everything.
DRY_RUN = False

# Delay between emails
DELAY = 4

# Gmail SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize(text):
    """
    Normalizes names for safe certificate matching.

    Example:

    'Rahul Patel'
    'rahul_patel'
    'RAHUL-PATEL'

    all become:

    'rahulpatel'
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(text).lower()
    )


# ============================================================
# FIND CERTIFICATE
# ============================================================

def find_certificate(name):

    target = normalize(name)

    if not os.path.exists(CERTIFICATE_FOLDER):
        return None

    for filename in os.listdir(CERTIFICATE_FOLDER):

        # Only PNG files
        if not filename.lower().endswith(".png"):
            continue

        filename_without_extension = os.path.splitext(
            filename
        )[0]

        if normalize(filename_without_extension) == target:

            return os.path.join(
                CERTIFICATE_FOLDER,
                filename
            )

    return None


# ============================================================
# LOAD ALREADY SENT EMAILS
# ============================================================

def load_sent_emails():

    sent = set()

    if not os.path.exists(SENT_FILE):
        return sent

    try:

        with open(
            SENT_FILE,
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                email = row.get(
                    "Email",
                    ""
                ).strip().lower()

                if email:
                    sent.add(email)

    except Exception as error:

        print(
            f"Warning: Could not read {SENT_FILE}: {error}"
        )

    return sent


# ============================================================
# SAVE RESULT TO CSV
# ============================================================

def save_result(filename, row):

    fieldnames = [
        "Name",
        "Enrollment Number",
        "Email",
        "Certificate",
        "Status",
        "Error"
    ]

    file_exists = os.path.exists(filename)

    with open(
        filename,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# ============================================================
# CREATE EMAIL
# ============================================================

def create_email(
    sender_email,
    name,
    recipient_email,
    certificate_path
):

    message = EmailMessage()

    # --------------------------------------------------------
    # Email headers
    # --------------------------------------------------------

    message["From"] = sender_email
    message["To"] = recipient_email

    message["Subject"] = (
        "Certificate of Participation – CONCEIT 2.0"
    )

    # --------------------------------------------------------
    # Plain text email
    # --------------------------------------------------------

    plain_text = f"""
Dear {name},

Thank you for actively participating in CONCEIT 2.0,
the second edition of the flagship technical speaker
series organized by MBIT IEEE SB.

Please find your Certificate of Participation attached
to this email.

We appreciate your participation and look forward to
seeing you at our upcoming initiatives.

Regards,
MBIT IEEE Student Branch
Madhuben & Bhanubhai Patel Institute of Technology
"""

    message.set_content(
        plain_text
    )

    # --------------------------------------------------------
    # HTML email
    # --------------------------------------------------------

    html = f"""
<html>
<head>
    <meta charset="UTF-8">
</head>

<body>

<p>Dear <b>{name}</b>,</p>

<p>
Thank you for actively participating in
<b>CONCEIT 2.0</b>, the second edition of the
flagship technical speaker series organized by
<b>MBIT IEEE SB</b>.
</p>

<p>
Please find your <b>Certificate of Participation</b>
attached to this email.
</p>

<p>
We appreciate your participation and look forward
to seeing you at our upcoming initiatives.
</p>

<br>

<p>
Regards,<br>
<b>MBIT IEEE Student Branch</b><br>
Madhuben & Bhanubhai Patel Institute of Technology
</p>

</body>
</html>
"""

    message.add_alternative(
        html,
        subtype="html"
    )

    # --------------------------------------------------------
    # Attach PNG certificate
    # --------------------------------------------------------

    with open(
        certificate_path,
        "rb"
    ) as file:

        certificate_data = file.read()

    message.add_attachment(
        certificate_data,
        maintype="image",
        subtype="png",
        filename=os.path.basename(
            certificate_path
        )
    )

    return message


# ============================================================
# START PROGRAM
# ============================================================

print()
print("=" * 55)
print("       CONCEIT 2.0 CERTIFICATE SENDER")
print("=" * 55)
print()


# ============================================================
# CHECK CSV
# ============================================================

if not os.path.exists(CSV_FILE):

    print("ERROR: CSV file not found.")
    print()
    print(f"Expected file:")
    print(CSV_FILE)

    input("\nPress Enter to exit...")
    exit()


# ============================================================
# CHECK CERTIFICATE FOLDER
# ============================================================

if not os.path.exists(CERTIFICATE_FOLDER):

    print("ERROR: Certificate folder not found.")
    print()
    print(f"Expected folder:")
    print(CERTIFICATE_FOLDER)

    input("\nPress Enter to exit...")
    exit()


# ============================================================
# GET GMAIL DETAILS
# ============================================================

SENDER_EMAIL = input(
    "Your college Gmail address: "
).strip()

APP_PASSWORD = getpass.getpass(
    "Gmail App Password: "
)


# ============================================================
# READ PARTICIPANTS
# ============================================================

try:

    with open(
        CSV_FILE,
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        participants = list(reader)

except Exception as error:

    print()
    print("ERROR: Could not read CSV.")
    print(error)

    input("\nPress Enter to exit...")
    exit()


# ============================================================
# VALIDATE CSV COLUMNS
# ============================================================

required_columns = [
    "Name of Student",
    "Enrollment Number"
]

missing_columns = [
    column
    for column in required_columns
    if column not in reader.fieldnames
]

if missing_columns:

    print()
    print("ERROR: CSV is missing required columns:")

    for column in missing_columns:
        print(f" - {column}")

    print()
    print("Found columns:")
    print(reader.fieldnames)

    input("\nPress Enter to exit...")
    exit()


# ============================================================
# LOAD PREVIOUSLY SENT EMAILS
# ============================================================

sent_emails = load_sent_emails()


# ============================================================
# INITIAL REPORT
# ============================================================

print()
print("-" * 55)

print(
    f"Participants found : {len(participants)}"
)

print(
    f"Already sent       : {len(sent_emails)}"
)

print(
    f"Certificate folder : {CERTIFICATE_FOLDER}"
)

print(
    f"Dry run            : {DRY_RUN}"
)

print("-" * 55)
print()


# ============================================================
# COUNTERS
# ============================================================

sent_count = 0
failed_count = 0
missing_count = 0
duplicate_count = 0


# ============================================================
# SMTP CONNECTION
# ============================================================

server = None

if not DRY_RUN:

    try:

        print("Connecting to Gmail...")

        server = smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        print("Gmail login successful.")
        print()

    except Exception as error:

        print()
        print("=" * 55)
        print("ERROR: Gmail login failed.")
        print("=" * 55)
        print()
        print(error)
        print()

        input("Press Enter to exit...")
        exit()


# ============================================================
# PROCESS EVERY PARTICIPANT
# ============================================================

for index, participant in enumerate(
    participants,
    start=1
):

    print("-" * 55)

    print(
        f"[{index}/{len(participants)}]"
    )

    # --------------------------------------------------------
    # Read name
    # --------------------------------------------------------

    name = participant[
        "Name of Student"
    ].strip()

    # --------------------------------------------------------
    # Read enrollment number
    # --------------------------------------------------------

    enrollment = str(
        participant[
            "Enrollment Number"
        ]
    ).strip()

    # --------------------------------------------------------
    # Create college email
    # --------------------------------------------------------

    email = (
        enrollment
        + EMAIL_DOMAIN
    )

    print(
        f"Name       : {name}"
    )

    print(
        f"Enrollment : {enrollment}"
    )

    print(
        f"Email      : {email}"
    )

    # --------------------------------------------------------
    # Check duplicate
    # --------------------------------------------------------

    if email.lower() in sent_emails:

        print(
            "Status     : SKIPPED - Already sent"
        )

        duplicate_count += 1

        continue

    # --------------------------------------------------------
    # Find certificate
    # --------------------------------------------------------

    certificate = find_certificate(
        name
    )

    if certificate is None:

        print(
            "Status     : SKIPPED - Certificate missing"
        )

        save_result(
            FAILED_FILE,
            {
                "Name": name,
                "Enrollment Number": enrollment,
                "Email": email,
                "Certificate": "",
                "Status": "Certificate Missing",
                "Error": "PNG certificate not found"
            }
        )

        missing_count += 1

        continue

    print(
        "Certificate: "
        + os.path.basename(certificate)
    )

    # --------------------------------------------------------
    # Create email
    # --------------------------------------------------------

    message = create_email(
        SENDER_EMAIL,
        name,
        email,
        certificate
    )

    # --------------------------------------------------------
    # DRY RUN
    # --------------------------------------------------------

    if DRY_RUN:

        print(
            "Status     : DRY RUN - Not sent"
        )

        continue

    # --------------------------------------------------------
    # SEND EMAIL
    # --------------------------------------------------------

    try:

        server.send_message(
            message
        )

        print(
            "Status     : SUCCESS - Email sent"
        )

        # Save successful send
        save_result(
            SENT_FILE,
            {
                "Name": name,
                "Enrollment Number": enrollment,
                "Email": email,
                "Certificate": os.path.basename(
                    certificate
                ),
                "Status": "Sent",
                "Error": ""
            }
        )

        sent_emails.add(
            email.lower()
        )

        sent_count += 1

        # ----------------------------------------------------
        # Delay
        # ----------------------------------------------------

        time.sleep(
            DELAY
        )

    except Exception as error:

        print(
            "Status     : FAILED"
        )

        print(
            f"Error      : {error}"
        )

        save_result(
            FAILED_FILE,
            {
                "Name": name,
                "Enrollment Number": enrollment,
                "Email": email,
                "Certificate": os.path.basename(
                    certificate
                ),
                "Status": "Failed",
                "Error": str(error)
            }
        )

        failed_count += 1


# ============================================================
# CLOSE GMAIL CONNECTION
# ============================================================

if server:

    try:
        server.quit()
    except Exception:
        pass


# ============================================================
# FINAL REPORT
# ============================================================

print()
print()
print("=" * 55)
print("                  FINAL REPORT")
print("=" * 55)

print()
print(
    f"Total participants : {len(participants)}"
)

print(
    f"Sent successfully  : {sent_count}"
)

print(
    f"Failed             : {failed_count}"
)

print(
    f"Certificate missing: {missing_count}"
)

print(
    f"Already sent       : {duplicate_count}"
)

print()
print("-" * 55)

print(
    f"Sent report   : {SENT_FILE}"
)

print(
    f"Failed report : {FAILED_FILE}"
)

print("-" * 55)

print()
print("DONE 🎉")
print()

input("Press Enter to exit...")