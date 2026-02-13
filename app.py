import os
import json
import base64
from datetime import datetime
from email.mime.text import MIMEText
from calendar import monthrange

from flask import Flask, render_template, request, redirect, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup   # ✅ moved here

app = Flask(__name__)

# ================= CONFIG =================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

CATEGORY_FILE = "categories.json"
EMAIL_CACHE   = "emails.json"
REMINDER_FILE = "reminders.json"

MAX_EMAILS = 120
TEXT_LIMIT = 1500

# ================= UTILITIES =================

def safe_json_load(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=2)
        return default

    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default


def safe_json_save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ================= CATEGORIES =================

def load_categories():
    return safe_json_load(
        CATEGORY_FILE,
        ["Academics", "Job", "Travel", "Shopping", "Personal"]
    )

# ================= GMAIL AUTH =================

def gmail():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# ================= EMAIL PARSING =================

def extract_body(payload):
    plain = ""
    html  = ""

    def walk(parts):
        nonlocal plain, html
        for p in parts:
            mime = p.get("mimeType", "")
            data = p.get("body", {}).get("data")

            if data:
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
                if mime == "text/plain":
                    plain += decoded
                elif mime == "text/html":
                    html += decoded

            if "parts" in p:
                walk(p["parts"])

    if "parts" in payload:
        walk(payload["parts"])
    else:
        data = payload.get("body", {}).get("data")
        if data:
            plain = base64.urlsafe_b64decode(data).decode("utf-8", "ignore")

    return plain.strip(), html.strip()

def extract_headers(msg):
    headers = {"from": "Unknown", "subject": "(No subject)", "date": ""}
    for h in msg["payload"].get("headers", []):
        name = h["name"].lower()
        if name in headers:
            headers[name] = h["value"]
    return headers

# ================= CLASSIFIER =================

def classify(text, labels):
    t = text.lower()
    for l in labels:
        if l.lower() in t:
            return l
        if l == "Job" and any(x in t for x in ["career","interview","hr","hiring"]):
            return l
        if l == "Travel" and any(x in t for x in ["flight","hotel","trip","booking"]):
            return l
        if l == "Academics" and any(x in t for x in ["exam","college","course"]):
            return l
    return "Others"

# ================= FETCH EMAILS =================

def fetch_emails(force=False):
    if os.path.exists(EMAIL_CACHE) and not force:
        data = safe_json_load(EMAIL_CACHE, [])
        if data:
            return

    service = gmail()
    labels  = load_categories() + ["Others"]
    mails   = []

    res = service.users().messages().list(
        userId="me",
        maxResults=MAX_EMAILS
    ).execute()

    for m in res.get("messages", []):
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="full"
        ).execute()

        plain, html = extract_body(msg["payload"])
        head = extract_headers(msg)

        mails.append({
            "id": m["id"],
            "category": classify(plain or html, labels),
            "from": head["from"],
            "subject": head["subject"],
            "date": head["date"],
            "plain": plain[:TEXT_LIMIT],
            "html": html
        })

    safe_json_save(EMAIL_CACHE, mails)

# ================= ROUTES =================

@app.route("/")
def index():
    fetch_emails()

    mails  = safe_json_load(EMAIL_CACHE, [])
    labels = load_categories() + ["Others"]

    folders = {l: [] for l in labels}
    for m in mails:
        folders[m["category"]].append(m)

    return render_template("index.html", folders=folders)

@app.route("/refresh")
def refresh():
    fetch_emails(force=True)
    return redirect("/")

@app.route("/folder/<name>")
def folder(name):
    mails = safe_json_load(EMAIL_CACHE, [])
    emails = [m for m in mails if m["category"] == name]
    return render_template("folder.html", name=name, emails=emails)

@app.route("/mail/<mail_id>")
def view_mail(mail_id):
    mails = safe_json_load(EMAIL_CACHE, [])
    mail = next((m for m in mails if m["id"] == mail_id), None)
    if not mail:
        return "Mail not found", 404
    return render_template("mail_view.html", mail=mail)

@app.route("/compose")
def compose():
    return render_template("compose.html")


# ================= SUMMARY =================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json or {}

    text = data.get("text", "")
    html_content = data.get("html", "")

    # If only HTML content exists (structured emails)
    if not text and html_content:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(" ")

    text = text.strip()

    if not text:
        return jsonify({
            "summary": "No content available for summarization."
        })

    # Simple summary logic
    sentences = text.replace("\n", " ").split(". ")

    summary = ". ".join(sentences[:2]).strip()

    if not summary.endswith("."):
        summary += "."

    return jsonify({
        "summary": summary
    })


# ================= SEND =================

@app.route("/send_mail", methods=["POST"])
def send():
    d = request.json

    if not d.get("to") or not d.get("body"):
        return jsonify({"status": "error", "msg": "Missing fields"})

    msg = MIMEText(d["body"], "html")
    msg["to"] = d["to"]
    msg["subject"] = d.get("subject", "Mail")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    gmail().users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    return jsonify({"status": "sent"})

# ================= ADD FOLDER =================

@app.route("/add_folder", methods=["POST"])
def add_folder():
    name = request.form.get("name", "").strip()

    if not name:
        return redirect("/")

    categories = load_categories()

    if name not in categories:
        categories.append(name)
        safe_json_save(CATEGORY_FILE, categories)

    return redirect("/")

# ================= RUN =================

if __name__ == "__main__":
    print("🚀 Smart Gmail AI Running...")
    app.run(debug=True)
