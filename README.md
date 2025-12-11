# Batch Email Sender

A simplistic, efficient Python script for sending personalized mass emails with attachments. It features automatic logging and manages the recipient list by removing successfully contacted addresses.

## Features

- **Personalized Sending**: Sends individual emails to a list of recipients.
- **Attachment Support**: Automatically attaches all files found in the `resume/` directory.
- **State Management**: Automatically removes successfully emailed recipients from the input CSV to prevent duplicate sends on re-runs.
- **Logging**: Records every sent email in `sent-mails/sent-mails.csv` with a timestamp.
- **Template System**: Uses a simple text file for email subject and body.

## Prerequisites

- [Python 3.14+](https://www.python.org/downloads/)
- An email account (Gmail recommended) with App Password enabled.

## Project Structure

```
send-email/
├── email-list.csv          # Input list of recipients
├── main.py                 # Main application script
├── README.md               # Project documentation
├── pyproject.toml          # Project metadata and dependencies
├── resume/                 # Directory for attachments
│   └── (Put files here)
├── sent-mails/             # Output directory for logs
│   └── sent-mails.csv      # Log of sent emails
└── template/
    └── email_body.txt      # Email content template
```

## Setup

1. **Prepare Recipient List**:
   - Edit `email-list.csv`.
   - The first column must contain the email addresses.
   - Example:
     ```csv
     Email,Name
     test@example.com,John Doe
     ```

2. **Prepare Email Template**:
   - Edit `template/email_body.txt`.
   - The first line must start with `Subject:`.
   - The rest of the file is the email body.
   - Example:
     ```text
     Subject: Application for Software Engineer

     Dear Hiring Manager,

     Please find attached my resume...
     ```

3. **Add Attachments**:
   - Place any files you want to attach (e.g., PDF resume, cover letter) inside the `resume/` directory.

## Configuration

pre-requsites: install uv astral
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
reference link: https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2

Now install dependencies: by running below cmd
```
uv sync 
```

Open `main.py` and update the configuration section at the top:

```python
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
```

> [!IMPORTANT]
> **For Gmail Users**: You must use an **App Password**, not your regular login password.
> 1. Go to your [Google Account](https://myaccount.google.com/).
> 2. Search for "App Passwords".
> 3. Create a new app password and paste it into `SENDER_PASSWORD`.

## Usage

Run the script using Python:

```bash
python main.py
```

### What happens when you run it?
1. The script reads the subject and body from `template/email_body.txt`.
2. It gathers all files from `resume/` to attach.
3. It iterates through `email-list.csv`.
4. For each recipient:
   - Sends the email.
   - Logs the success in `sent-mails/sent-mails.csv`.
   - Records the recipient to be removed from the list.
5. After processing all recipients, it **updates `email-list.csv`** by removing the rows of people who were successfully emailed.

> [!NOTE]
> If an email fails to send, that recipient remains in `email-list.csv` so you can try again later.
