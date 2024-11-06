import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from mimetypes import guess_type as guess_mime_type


def gmail_authenticate(scopes, auth_json = "auth.json", auth_pickle = "auth.pickle"):
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists(auth_pickle):
        with open(auth_pickle, "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(auth_json, scopes)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(auth_pickle, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def build_message(destination, from_email, obj, body, attachments=[]):
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = from_email
        message['subject'] = obj
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, destination, from_email, obj, body, attachments=[]):
    return service.users().messages().send(
    userId="me",
    body=build_message(destination, from_email, obj, body, attachments)
    ).execute()

def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def parse_parts(service, parts):
    """
    Utility function that parses the content of an email partition
    """
    email_body = {"plain": [], "html":[]}
    if parts:
        for part in parts:
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                sub_part = parse_parts(service, part.get("parts"))
                for new_plain in sub_part["plain"]:
                    email_body["plain"].append(new_plain)
                for new_html in sub_part["html"]:
                    email_body["html"].append(new_html)

            if mimeType == "text/plain":
                # if the email part is text plain
                if data:
                    text = urlsafe_b64decode(data).decode()
                    email_body["plain"].append(text)
            elif mimeType == "text/html":
                # if the email part is an HTML content
                # save the HTML file and optionally open it in the browser
                if data:
                    html = urlsafe_b64decode(data).decode()
                    email_body["html"].append(html)
            else:
                # attachment other than a plain text or HTML
                print("Received unknown attachment")
    return email_body

def read_message(service, message_id):
    """
    """
    email_data = {}
    msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    # parts can be the message body, or attachments
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    folder_name = "email"
    if headers:
        for header in headers:
            email_data[header["name"]] = header["value"]

    email_data["Message-Body"] = parse_parts(service, parts)
    return email_data
