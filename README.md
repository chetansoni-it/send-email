# Send Email Script (Deprecated)

This folder contains the original email sending script.

> **⚠️ DEPRECATED**: The email sending logic has been ported to the `backend/` application.
> Please use the backend API (`POST /trigger-emails`) instead of running this script directly.

## Legacy Usage

This script was used to:
1.  Read `email-list.csv`.
2.  Send emails using `template/email_body.txt`.
3.  Attach resume automatically.

Now, all these features are available in the backend with:
-   **API Access**: Trigger via HTTP.
-   **Background Processing**: Non-blocking.
-   **Unified Storage**: Reads from the main database/csv.
