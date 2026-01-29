# Anti Spam Helper

A Chrome extension that detects suspicious URLs in Gmail and reports them to a central server for spam protection.

## Installation

This folder contains the browser extension files that can be loaded directly into Chrome or Chromium.

1. Open Chrome (or Chromium) and go to `chrome://extensions`.
2. Enable "Developer mode" (top right).
3. Click "Load unpacked" and select the `anti-spam-extension/` folder.

## How It Works

- **Background service worker**: Runs in the background and handles all messages from the content script and popup. It communicates with the central server to check URLs and submit spam complaints.

- **Content script**: Automatically runs when you open Gmail. It extracts URLs from emails and sends them to the background worker for verification against the spam database.

- **Popup UI**: A small interface that appears in your browser toolbar. It displays the spam detection status for the current email and allows you to manually report suspicious emails as spam.

- **Options page**: Allows you to configure the extension settings, including the central server URL and other preferences.

- **Common utilities**: Shared modules for secure storage of settings using Chrome's storage API and for making API calls to the central server.
