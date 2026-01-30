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

# List of common public email providers to exclude from company domain matching
COMMON_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 
    'aol.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'mail.com',
    'msn.com', 'live.com', 'me.com', 'googlemail.com', 'rocketmail.com',
    'btinternet.com', 'comcast.net', 'verizon.net', 'cox.net'
}

def get_sent_data(sent_file):
    """Reads the sent-mails CSV and returns a set of emails and a set of company domains."""
    sent_emails = set()
    sent_domains = set()
    
    if os.path.exists(sent_file):
        try:
            with open(sent_file, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header
                for row in reader:
                    if row and len(row) > 0:
                        email = row[0].strip().lower()
                        if email and '@' in email:
                            sent_emails.add(email)
                            domain = email.split('@')[-1]
                            if domain and domain not in COMMON_DOMAINS:
                                sent_domains.add(domain)
        except Exception as e:
            print(f"Warning: Could not read {sent_file}: {e}")
            
    return sent_emails, sent_domains


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

    # 2.5. Check for duplicates and company matches in sent-mails.csv
    sent_emails, sent_domains = get_sent_data(SENT_EMAILS_FILE)
    
    duplicates = []
    company_matches = []
    clean_recipients = []
    
    for item in recipients_to_send:
        email = item['email'].lower()
        domain = email.split('@')[-1] if '@' in email else ""
        
        if email in sent_emails:
            duplicates.append(item)
        elif domain and domain in sent_domains:
            company_matches.append(item)
        else:
            clean_recipients.append(item)
            
    successful_row_indices = [] # To keep track of rows to remove from CSV
    
    if duplicates or company_matches:
        if duplicates:
            print(f"\n[!] The following emails are already in {SENT_EMAILS_FILE}:")
            for d in duplicates:
                print(f"    - {d['email']}")
        
        if company_matches:
            print(f"\n[!] The following emails belong to companies you've already contacted:")
            for c in company_matches:
                print(f"    - {c['email']}")
                
        choice = input("\nDo you want to remove these from email-list.csv and skip sending? (y/n): ").strip().lower()
        if choice == 'y':
            print("Cleaning list...")
            skipped_indices = [d['row_index'] for d in duplicates] + [c['row_index'] for c in company_matches]
            successful_row_indices.extend(skipped_indices)
            recipients_to_send = clean_recipients
            
    if not recipients_to_send:
        if not successful_row_indices:
            print("No new recipients to process.")
            return
        else:
            print("All recipients were removed as duplicates/already contacted. Proceeding to update the CSV file.")
    else:
        print(f"Found {len(recipients_to_send)} recipient(s) to process.")

    # 3. Connect to SMTP Server
    try:
        if recipients_to_send:
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
            
            # Create a new list of rows to keep (those not successfully sent or intentionally skipped)
            indices_to_remove = set(successful_row_indices)
            rows_to_keep = [row for i, row in enumerate(all_rows) if i not in indices_to_remove]
            
            # Write the remaining rows back to the original CSV file
            with open(EMAIL_LIST_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows_to_keep)
                
            print(f"Successfully updated {EMAIL_LIST_FILE}. {len(rows_to_keep) - 1} recipient(s) remaining.")
        else:
            print("No changes needed for the recipient list.")



    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect or log in to SMTP server. Error: {e}")

if __name__ == "__main__":
    send_emails()