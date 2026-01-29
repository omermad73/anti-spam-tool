# Anti-Spam Email Project

This project is for detecting spam emails and DDoS attacking spam websites using a browser extension and centralized server infrastructure. It is inspired by an anti-spam tool from the 2000s called BlueFrog.

This project is part of a Mini Project on Network Security course at BGU.

## Project Overview

The system consists of multiple components working together to protect Gmail users from spam:

1. **Anti-Spam Extension** (`anti-spam-extension/`): A Chrome browser extension that automatically detects suspicious URLs in Gmail and reports them
2. **Central Server** (`server/`): Backend service that manages spam databases and processes URL verification requests
3. **Complaint Dashboard** (`spam_websites/`): Real-time web interface displaying incoming spam complaints
4. **Email Spammer** (`spammer/`): Tool for sending bulk emails (for testing/educational purposes)

The Anti-Spam Extension and the Central Server are the core anti-spam components, while the Complaint Dashboard and Email Spammer are for testing and simulation.

See individual README files in each directory for detailed instructions.
