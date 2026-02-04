import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import csv
import os
from datetime import datetime
import glob
import re

# --- Configuration ---
SENDER_EMAIL = "chetansoni9991@gmail.com"  # **CHANGE THIS**
SENDER_PASSWORD = "hhgs znac mbuf bcqx"  # **CHANGE THIS to your Gmail App Password**
# If you don't use an App Password, you must enable "Less secure app access" 
# and use your regular password (Not recommended).

EMAIL_LIST_PATTERN = "new-mails/linkedin_posts*.csv"
SENT_EMAILS_FILE = "sent-mails/sent-mails.csv" # New output file path
TEMPLATE_FILE = "template/email_body.txt"
ATTACHMENT_DIR = "resume/"
PORTFOLIO_LINK = "https://chetansoni-it.github.io/chetansoni-it/"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for TLS

# List of common public email providers to exclude from company domain matching
COMMON_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 
    'aol.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'mail.com',
    'msn.com', 'live.com', 'me.com', 'googlemail.com', 'rocketmail.com',
    'btinternet.com', 'comcast.net', 'verizon.net', 'cox.net', 'att.net',
    'sbcglobal.net', 'bellsouth.net', 'charter.net', 'shaw.ca', 'earthlink.net',
    'mail.ru', 'gmx.com', 'gmx.de', 'web.de', 't-online.de', 'libero.it',
    'virgilio.it', 'alice.it', 'wanadoo.fr', 'orange.fr', 'free.fr', 'laposte.net',
    'rediffmail.com', 'indiatimes.com', 'tiscali.it', 'uol.com.br', 'bol.com.br',
    'terra.com.br', 'ig.com.br', 'globomail.com', 'oi.com.br', 'sky.com',
    'virginmedia.com', 'ntlworld.com', 'blueyonder.co.uk', 'talktalk.net'
}

def get_base_domain(domain):
    """Simple helper to get the base domain for comparison (e.g., mail.google.com -> google.com)."""
    if not domain:
        return ""
    parts = domain.split('.')
    if len(parts) > 2:
        # Check for common multi-part TLDs like .co.uk, .com.br, etc.
        if parts[-2] in ('com', 'co', 'org', 'net', 'edu', 'gov', 'ac') and len(parts) >= 3:
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])
    return domain

def get_sent_data(sent_file):
    """Reads the sent-mails CSV and returns a set of emails and a mapping of domains to contacted emails."""
    sent_emails = set()
    sent_domains_map = {} # domain -> list of emails contacted at that domain
    
    if os.path.exists(sent_file):
        try:
            # Use utf-8-sig to handle possible BOM from Excel
            with open(sent_file, mode='r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Peek at the first row to check if it's a header
                try:
                    first_row = next(reader)
                    if first_row:
                        # If the first row looks like an email, treat it as data, not header
                        if '@' in first_row[0]:
                            process_row(first_row, sent_emails, sent_domains_map)
                        # Otherwise it's likely a header, we skip it (already consumed by next())
                except StopIteration:
                    pass # Empty file
                    
                for row in reader:
                    process_row(row, sent_emails, sent_domains_map)
        except Exception as e:
            print(f"Warning: Could not read {sent_file}: {e}")
            
    return sent_emails, sent_domains_map

def process_row(row, sent_emails, sent_domains_map):
    """Helper to process a single row from the sent-mails CSV."""
    if row and len(row) > 0:
        email = row[0].strip().lower()
        if email and '@' in email:
            sent_emails.add(email)
            domain = email.split('@')[-1]
            if domain and domain not in COMMON_DOMAINS:
                if domain not in sent_domains_map:
                    sent_domains_map[domain] = []
                if email not in sent_domains_map[domain]:
                    sent_domains_map[domain].append(email)
                
                # Also track base domain for subdomain matching
                base = get_base_domain(domain)
                if base and base != domain:
                    if base not in sent_domains_map:
                        sent_domains_map[base] = []
                    if email not in sent_domains_map[base]:
                        sent_domains_map[base].append(email)




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

def create_message(recipient_email, subject, body, attachments, metadata=None):
    """Creates an email message (MIMEMultipart) with text and attachments.
    
    Args:
        recipient_email: The recipient's email address
        subject: Email subject
        body: Email body template
        attachments: List of file paths to attach
        metadata: Dict containing author, content, contact_numbers, apply_links from LinkedIn post
    """
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    # Build the full email body with portfolio link and reference info
    full_body = body
    
    # Add portfolio link with emphasis
    full_body += "\n\n" + "★" * 50
    full_body += f"\n\n📌 MY PORTFOLIO: {PORTFOLIO_LINK}\n"
    full_body += "★" * 50
    
    # Add reference info from LinkedIn post if available
    if metadata:
        full_body += "\n\n" + "="*50
        full_body += "\n[Reference - LinkedIn Post Details]"
        full_body += "\n" + "="*50
        
        if metadata.get('author'):
            full_body += f"\nPosted by: {metadata['author']}"
        
        if metadata.get('content'):
            # Include full content - no truncation for complete backup
            full_body += f"\n\nPost Content:\n{metadata['content']}"
        
        if metadata.get('contact_numbers'):
            full_body += f"\n\nContact Numbers: {metadata['contact_numbers']}"
        
        if metadata.get('apply_links'):
            full_body += f"\n\nApply Links: {metadata['apply_links']}"
        
        full_body += "\n" + "="*50
    
    msg.attach(MIMEText(full_body, 'plain'))

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


def log_sent_email(recipient, sent_file, metadata=None):
    """Appends the recipient email, timestamp, and LinkedIn post metadata to the sent-mails log file.
    
    Args:
        recipient: The recipient's email address
        sent_file: Path to the sent-mails CSV file
        metadata: Dict containing author, content, contact_numbers, apply_links from LinkedIn post
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(sent_file), exist_ok=True)
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(sent_file)
    
    with open(sent_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header only if the file is newly created
        if not file_exists or os.path.getsize(sent_file) == 0:
            writer.writerow(['Recipient Email', 'Date Sent', 'Author', 'Contact Numbers', 'Apply Links', 'Content'])
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract metadata or use empty strings
        author = metadata.get('author', '') if metadata else ''
        contact_numbers = metadata.get('contact_numbers', '') if metadata else ''
        apply_links = metadata.get('apply_links', '') if metadata else ''
        content = metadata.get('content', '') if metadata else ''
        
        writer.writerow([recipient, current_time, author, contact_numbers, apply_links, content])

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
    all_files_data = {} # file_path -> list of rows
    recipients_to_send = []
    
    file_paths = glob.glob(EMAIL_LIST_PATTERN)
    if not file_paths:
        print(f"Error: No recipient lists found matching {EMAIL_LIST_PATTERN}")
        return

    for file_path in file_paths:
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader, None)
                if not header:
                    continue
                
                all_files_data[file_path] = [header]
                
                # Find the index of required columns
                header_lower = [h.strip().lower() for h in header]
                if "emails" not in header_lower:
                    print(f"Warning: 'emails' column not found in {file_path}. Skipping.")
                    continue
                
                email_col_idx = header_lower.index("emails")
                
                # Find optional metadata columns
                author_idx = header_lower.index("author") if "author" in header_lower else None
                contact_idx = header_lower.index("contact_numbers") if "contact_numbers" in header_lower else None
                apply_idx = header_lower.index("apply_links") if "apply_links" in header_lower else None
                content_idx = header_lower.index("content") if "content" in header_lower else None
                
                for row in reader:
                    all_files_data[file_path].append(row)
                    if row and len(row) > email_col_idx:
                        email_cell = row[email_col_idx].strip()
                        if email_cell:
                            # Extract metadata from the row
                            metadata = {
                                'author': row[author_idx].strip() if author_idx is not None and len(row) > author_idx else '',
                                'contact_numbers': row[contact_idx].strip() if contact_idx is not None and len(row) > contact_idx else '',
                                'apply_links': row[apply_idx].strip() if apply_idx is not None and len(row) > apply_idx else '',
                                'content': row[content_idx].strip() if content_idx is not None and len(row) > content_idx else ''
                            }
                            
                            # Split multiple emails by comma or space
                            # We look for anything that looks like an email
                            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email_cell)
                            for email in found_emails:
                                recipients_to_send.append({
                                    'email': email.lower().strip(),
                                    'row_index': len(all_files_data[file_path]) - 1,
                                    'file_path': file_path,
                                    'metadata': metadata
                                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    if not recipients_to_send:
        print("No new recipients found in the CSV files.")
        return

    # 2.5. Check for duplicates and company matches in sent-mails.csv
    sent_emails, sent_domains_map = get_sent_data(SENT_EMAILS_FILE)
    
    duplicates = []
    company_matches = [] # list of tuples (new_item, matched_previous_email)
    clean_recipients = []
    
    for item in recipients_to_send:
        email = item['email'].lower()
        domain = email.split('@')[-1] if '@' in email else ""
        base_domain = get_base_domain(domain)
        
        if email in sent_emails:
            duplicates.append(item)
        elif domain and domain in sent_domains_map:
            # Direct domain match
            company_matches.append((item, sent_domains_map[domain][0]))
        elif base_domain and base_domain in sent_domains_map:
            # Base domain match (handles subdomains)
            company_matches.append((item, sent_domains_map[base_domain][0]))
        else:
            clean_recipients.append(item)
            
    # To keep track of (file_path, row_index) to remove from CSVs
    successful_removals = set()
    
    if duplicates or company_matches:
        if duplicates:
            print(f"\n[!] The following emails are already in {SENT_EMAILS_FILE}:")
            # Use a set to show unique emails in the warning
            for email_str in sorted(set(d['email'] for d in duplicates)):
                print(f"    - {email_str}")
        
        if company_matches:
            print(f"\n[!] The following emails belong to companies you've already contacted:")
            # Use a set to show unique emails in the warning
            for c_item, prev_email in company_matches:
                print(f"    - {c_item['email']} (Matches previous contact: {prev_email})")
                
        choice = input("\n[?] Found duplicates/previous company contacts. Remove those rows from source files and continue with others? (y/n): ").strip().lower()
        if choice == 'y':
            print("Cleaning list and moving forward...")
            for d in duplicates:
                successful_removals.add((d['file_path'], d['row_index']))
            for c_item, prev_email in company_matches:
                successful_removals.add((c_item['file_path'], c_item['row_index']))
            recipients_to_send = clean_recipients
        else:
            print("Aborting. No emails were sent. Please review your source files.")
            return

            
    if not recipients_to_send:
        if not successful_removals:
            print("No new recipients to process.")
            return
        else:
            print("All recipients were removed as duplicates/already contacted. Updating the source files.")

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
                file_path = recipient_data['file_path']
                metadata = recipient_data.get('metadata', {})
                
                msg = create_message(recipient_email, subject, body, attachments, metadata)
                
                try:
                    server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                    print(f"Successfully sent email to: {recipient_email}")
                    
                    # Log the sent email with metadata
                    log_sent_email(recipient_email, SENT_EMAILS_FILE, metadata)
                    
                    # Record the row to be removed
                    successful_removals.add((file_path, row_index))
                    
                except Exception as e:
                    print(f"Failed to send email to {recipient_email}. It will remain in the list. Error: {e}")
                    
            # 5. Close Connection
            server.quit()
            print("\n--- Processing Complete ---")
        
        # 6. Update the Source CSV files
        if successful_removals:
            # Group removals by file
            removals_by_file = {}
            for f_path, r_idx in successful_removals:
                if f_path not in removals_by_file:
                    removals_by_file[f_path] = set()
                removals_by_file[f_path].add(r_idx)
            
            for file_path, indices_to_remove in removals_by_file.items():
                print(f"Removing {len(indices_to_remove)} row(s) from {file_path}...")
                current_rows = all_files_data[file_path]
                rows_to_keep = [row for i, row in enumerate(current_rows) if i not in indices_to_remove]
                
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows_to_keep)
                print(f"Successfully updated {file_path}. {len(rows_to_keep) - 1} row(s) remaining.")
        else:
            print("No changes needed for the source files.")



    except Exception as e:
        print(f"\nFATAL ERROR: Could not connect or log in to SMTP server. Error: {e}")

if __name__ == "__main__":
    send_emails()