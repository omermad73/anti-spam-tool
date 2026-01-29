# Spam Complaint Dashboard

A real-time web dashboard that displays incoming spam complaints from the Anti Spam extension.

## Running the Dashboard

```bash
python3 listener.py
```

The dashboard will be available at `http://localhost:8787`

## How It Works

The dashboard receives spam complaints from the Anti Spam extension and displays them in real-time. It shows:
- Total count of complaints received
- A log of all suspicious URLs reported
- Real-time updates every second

You can reset all complaints with the "Clear All Complaints" button.
