# Email Spammer

A command-line tool for sending bulk emails using Gmail SMTP.

## Prerequisites

- Gmail account with 2-Factor Authentication enabled
- Gmail App Password (generate at https://myaccount.google.com/apppasswords)

## Usage

```bash
python3 spammer.py --email YOUR_EMAIL@gmail.com --password "YOUR_APP_PASSWORD"
```

## Options

- `--email`: Your Gmail address
- `--password`: Your Gmail App Password
- `--subject`: Custom subject line (optional)
- `--emails`: Path to JSON file with recipient emails (optional)
- `--message`: Path to message file (optional)
