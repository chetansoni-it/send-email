import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import csv
import os

# --- Configuration ---
SENDER_EMAIL = "chetansoni9991@gmail.com"  # **CHANGE THIS**
SENDER_PASSWORD = "hhgs znac mbuf bcqx"  # **CHANGE THIS to your Gmail App Password**
# If you don't use an App Password, you must enable "Less secure app access" 
# and use your regular password (Not recommended).

EMAIL_LIST_FILE = "email-list.csv"
TEMPLATE_FILE = "template/email_body.txt"
ATTACHMENT_DIR = "resume/"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for TLS

def read_template(template_path):
    """Reads the subject and body from the template file."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Assume the first line is the Subject, and the rest is the Body
        subject, *body_lines = content.split('\n', 1)
        body = '\n'.join(body_lines).strip()
        
        # Clean up the subject
        subject = subject.strip().replace("Subject:", "").strip()
        
        return subject, body
        
    except FileNotFoundError:
        print(f"Error: Template file not found at {template_path}")
        return None, None

def get_attachments(directory):
    """Gathers a list of full file paths for all files in the directory."""
    attachments = []
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                attachments.append(filepath)
    except FileNotFoundError:
        print(f"Warning: Attachment directory not found at {directory}")
    return attachments

def create_message(recipient_email, subject, body, attachments):
    """Creates an email message (MIMEMultipart) with text and attachments."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    # Attach the body text
    msg.attach(MIMEText(body, 'plain'))

    # Attach files
    for filepath in attachments:
        try:
            part = MIMEBase('application', 'octet-stream')
            with open(filepath, 'rb') as file:
                part.set_payload(file.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(filepath)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
            
        except Exception as e:
            print(f"Could not attach file {filepath}: {e}")

    return msg

def send_emails():
    """Main function to orchestrate reading files and sending emails."""
    print("--- Starting Email Script ---")
    
    # 1. Read Template
    subject, body = read_template(TEMPLATE_FILE)
    if not subject:
        return

    # 2. Get Attachments
    attachments = get_attachments(ATTACHMENT_DIR)
    if not attachments:
        print("No attachments found. Sending email without files.")
    else:
        print(f"Found {len(attachments)} attachment(s) to include.")

    # 3. Read Recipients
    recipients = []
    try:
        with open(EMAIL_LIST_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Assuming the CSV has a header row and email is in the first column
            next(reader, None) # Skip header row
            for row in reader:
                if row and '@' in row[0]: # Basic check for valid email
                    recipients.append(row[0].strip())
    except FileNotFoundError:
        print(f"Error: Recipient list CSV not found at {EMAIL_LIST_FILE}")
        return
    
    if not recipients:
        print("No recipients found in the CSV file.")
        return

    print(f"Found {len(recipients)} recipient(s) in the list.")
    
    # 4. Connect to SMTP Server
    try:
        # Connect to the server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls() # Secure the connection with TLS
        server.ehlo()
        
        # Log in
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # 5. Send Emails
        for recipient in recipients:
            msg = create_message(recipient, subject, body, attachments)
            
            try:
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                print(f"Successfully sent email to: {recipient}")
            except Exception as e:
                print(f"Failed to send email to {recipient}: {e}")
                
        # 6. Close Connection
        server.quit()
        print("--- Email Script Finished ---")

    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect or log in to SMTP server. Check your email/password or App Password. Error: {e}")

if __name__ == "__main__":
    send_emails()