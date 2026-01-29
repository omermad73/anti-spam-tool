# Central Server

The central server that manages spam URLs and processes complaints from the Anti Spam extension.

## Running the Server

```bash
python3 server.py
```

The server will start at `http://localhost:3000`

## How It Works

The server provides endpoints for:
- **URL Checking**: Receives URLs from the extension and checks them against the spam database
- **Complaint Handling**: Receives spam complaints from users and the dashboard
- **Email Filtering**: Filters out members from email lists to prevent targeting Anti Spam extension users
- **URL Management**: Maintains a database of known spam URLs

## Files

- `server.py`: Main server script
- `bad_urls.json`: Database of known spam URLs
- `members.json`: Hashed list of Anti Spam extension members
- `filter.html`: Web interface for filtering email lists
