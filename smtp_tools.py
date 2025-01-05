from email.mime.text import MIMEText
import json
import smtplib

def send_smtp_email(subject, body, recipient, auth_json = "auth.json"):
    sender = None
    auth_password = None
    with open(auth_json, "r") as f:
        auth = json.load(f)
        assert("user" in auth.keys())
        assert("password" in auth.keys())
        sender = auth["user"]
        auth_password = auth["password"]
    msg = MIMEText(body, "html")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, auth_password)
       smtp_server.sendmail(sender, recipient, msg.as_string())


if __name__=="__main__":
    send_smtp_email("Test", "12345", "robbarlw@gmail.com")
