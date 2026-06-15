import os
import imaplib
import email
import smtplib
from groq import Groq
from flask import Flask, render_template, request, jsonify
from collections import OrderedDict
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# client = Mistral(api_key=MISTRAL_API_KEY)
client = Groq(api_key=GROQ_API_KEY)
# client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.unread_emails = OrderedDict()

knowledge_base = ""

def fetch_unread_emails():
    """Fetch unread emails from Gmail via IMAP"""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        status, response = mail.search(None, '(UNSEEN)')
        unread_msg_nums = response[0].split()

        for e_id in unread_msg_nums:
            email_key = e_id.decode()
            
            if email_key in app.unread_emails:
                continue

            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get('subject', '(No Subject)')
                    from_ = msg.get('from', '(Unknown Sender)')

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')

                    draft = generate_reply(body)

                    app.unread_emails[email_key] = {
                        "id": email_key,
                        "from": from_,
                        "subject": subject,
                        "body": body,
                        "draft": draft
                    }
        
        mail.logout()
    except Exception as e:
        print(f"⚠️ IMAP Error: {e}")

def generate_reply(email_body):
    """Use AI to generate a polite customer support reply"""
    system_prompt = f"""You are a helpful, professional customer support assistant for TechFix IT Repairs. Your job is to reply to customer emails in a clear, polite, and solution-oriented way. Always provide helpful details, reassure the customer, and suggest next steps.

    Response Style Guidelines
    • Always be polite, professional, and empathetic.
    • Acknowledge the customer's issue before suggesting solutions.
    • Offer clear pricing ranges when possible.
    • Suggest next steps: visiting the shop, booking an appointment, or calling.
    • Sign off warmly with the business name.

    If relevant, use the knowledge base below:
    {knowledge_base}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_body}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return "Thank you for contacting TechFix IT Repairs. We have received your query and are looking into it."

def send_email(to_address, subject, body):
    """Send an email via Gmail SMTP"""
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_address
        msg.set_content(body)
        
        server.send_message(msg)

@app.route("/")
def index():
    fetch_unread_emails()
    return render_template('index.html', emails=app.unread_emails)

@app.route(rule='/send-email', methods=['POST'])
def send():
    data = request.json
    email_id = data.get('email_id')
    
    reply_body = data.get('reply') 
    
    email_data = app.unread_emails.get(email_id)
    if not email_data:
        return jsonify({'error': 'Email not found'}), 404
    
    to_address = email_data['from']
    subject = 'Re: ' + email_data['subject']
    
    if not reply_body:
        reply_body = email_data['draft']

    try:
        send_email(to_address, subject, reply_body)
        app.unread_emails.pop(email_id, None)
        return jsonify({"message": "Email sent successfully ✅"})
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

if __name__ == "__main__":
    try:
        with open('knowledge_base.txt', 'r') as f:
            knowledge_base = f.read()
    except FileNotFoundError:
        print("⚠️ Warning: knowledge_base.txt not found. Starting with empty knowledge base.")
        knowledge_base = ""
        
    app.run(debug=False)