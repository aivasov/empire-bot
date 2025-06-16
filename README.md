# Empire Quiz Admin

This is the admin panel for the Empire Quiz bot. It provides a web interface to manage quiz blocks, questions, and button texts.

## Requirements

- Python 3.10+
- Flask >= 2.0

## Installation

1. Clone or download the project archive.
2. Navigate to the project directory:
   ```bash
   cd empire-quiz-admin
   ```
3. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

- Edit `app.py` to set:
  - `app.secret_key` — a unique secret key for sessions.
  - `ADMIN_PASSWORD` — password for admin login.

## Running

```bash
python app.py
```

By default, the server listens on port 5000. Open your browser at `http://localhost:5000` to access the admin panel.

After making changes, click **Save** in the interface to persist data. The quiz data is stored in `data/questions.json`.

## Deployment

- For production, set `debug=False` in `app.run`.
- Use a production WSGI server (e.g., Gunicorn) and reverse proxy (e.g., NGINX) as needed.
