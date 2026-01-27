import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import csv
import os
from datetime import datetime # Import to get the current timestamp

# --- Configuration ---
SENDER_EMAIL = "chetansoni9991@gmail.com"  # **CHANGE THIS**
SENDER_PASSWORD = "hhgs znac mbuf bcqx"  # **CHANGE THIS to your Gmail App Password**
# If you don't use an App Password, you must enable "Less secure app access" 
# and use your regular password (Not recommended).

EMAIL_LIST_FILE = "email-list.csv"
SENT_EMAILS_FILE = "sent-mails/sent-mails.csv" # New output file path
TEMPLATE_FILE = "template/email_body.txt"
ATTACHMENT_DIR = "resume/"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for TLS

# (Functions read_template, get_attachments, and create_message remain UNCHANGED)

def read_template(template_path):
    """Reads the subject and body from the template file."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        subject, *body_lines = content.split('\n', 1)
        subject = subject.strip().replace("Subject:", "").strip()
        body = '\n'.join(body_lines).strip()
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
    
    msg.attach(MIMEText(body, 'plain'))

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


def log_sent_email(recipient, sent_file):
    """Appends the recipient email and timestamp to the sent-mails log file."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(sent_file), exist_ok=True)
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(sent_file)
    
    with open(sent_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header only if the file is newly created
        if not file_exists or os.path.getsize(sent_file) == 0:
            writer.writerow(['Recipient Email', 'Date Sent'])
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([recipient, current_time])

def send_emails():
    """Main function to orchestrate reading files, sending emails, logging, 
       and now, updating the recipient list."""
    print("--- Starting Email Script ---")
    
    # 1. Read Template and Attachments
    subject, body = read_template(TEMPLATE_FILE)
    if not subject:
        return

    attachments = get_attachments(ATTACHMENT_DIR)
    
    # 2. Read All Recipient Data and Identify Emails to Send
    all_rows = []
    recipients_to_send = []
    
    try:
        with open(EMAIL_LIST_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader, None) # Get and store the header row
            if header:
                all_rows.append(header)
                
            for row in reader:
                all_rows.append(row)
                if row and '@' in row[0]: # Assuming email is still in the first column
                    # Store the email along with its original row index for removal later
                    recipients_to_send.append({'email': row[0].strip(), 'row_index': len(all_rows) - 1})
    except FileNotFoundError:
        print(f"Error: Recipient list CSV not found at {EMAIL_LIST_FILE}")
        return
    
    if not recipients_to_send:
        print("No new recipients found in the CSV file.")
        return

    print(f"Found {len(recipients_to_send)} recipient(s) to process.")
    
    # List to track the row indices of successfully sent emails
    successful_row_indices = [] 
    
    # 3. Connect to SMTP Server
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # 4. Send Emails, Log Success, and Record Index
        for recipient_data in recipients_to_send:
            recipient_email = recipient_data['email']
            row_index = recipient_data['row_index']
            
            msg = create_message(recipient_email, subject, body, attachments)
            
            try:
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                print(f"Successfully sent email to: {recipient_email}")
                
                # Log the sent email
                log_sent_email(recipient_email, SENT_EMAILS_FILE)
                
                # Record the index of the row to be removed later
                successful_row_indices.append(row_index)
                
            except Exception as e:
                print(f"Failed to send email to {recipient_email}. It will remain in the list. Error: {e}")
                
        # 5. Close Connection
        server.quit()
        print("\n--- Processing Complete ---")
        
        # 6. Update the Recipient List CSV
        if successful_row_indices:
            print(f"Removing {len(successful_row_indices)} email(s) from {EMAIL_LIST_FILE}...")
            
            # Create a new list of rows to keep (those not successfully sent)
            # Use a set for quick lookup of indices to remove
            indices_to_remove = set(successful_row_indices)
            
            # Keep rows whose index is NOT in the set of successful indices
            rows_to_keep = [row for i, row in enumerate(all_rows) if i not in indices_to_remove]
            
            # Write the remaining rows back to the original CSV file
            with open(EMAIL_LIST_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows_to_keep)
                
            print(f"Successfully updated {EMAIL_LIST_FILE}. {len(rows_to_keep) - 1} recipient(s) remaining.")
        else:
            print("No emails were successfully sent, so the recipient list remains unchanged.")


    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect or log in to SMTP server. Error: {e}")

if __name__ == "__main__":
    send_emails()