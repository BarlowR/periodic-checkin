
import argparse
from datetime import datetime, timezone, timedelta
from enum import Enum
import markdown
import os
from gmail_tools import gmail_authenticate, send_message
from text_processor import process_text


# Need all access (permission to read/send/receive emails, manage the inbox, and more)
REQUIRED_SCOPES = ['https://mail.google.com/']
TIMEFORMAT = "%y-%m-%d-%H"
TIMEZONE = timezone(-timedelta(hours=7))

class Templates(str, Enum):
    YEARLY      = "yearly-template.md"
    MONTHLY     = "monthly-template.md"
    DAILY       = "daily-template.md"
    WEEKLY      = "weekly-template.md"

def parse_template(template_text):
    # TODO Replace bracketed text with value
    # Ex. {month} -> November
    processed_text = process_text(template_text)
    markdown_html_render = markdown.markdown(processed_text)
    return markdown_html_render

def format_datetime(current_time):
        year_value = current_time.strftime("%Y")
        month_value = current_time.strftime("%m")
        day_of_month_value = current_time.strftime("%d")

        return f"{year_value}-{month_value}-{day_of_month_value}"

parser = argparse.ArgumentParser()

if __name__ == "__main__":
    service = gmail_authenticate(REQUIRED_SCOPES)
    parser.add_argument("--to_email", required=True)
    parser.add_argument("--sender_email", required=True)

    parser.add_argument("--template_folder", default="templates")
    parser.add_argument("--periodic", default="weekly")
    args = parser.parse_args()

    checkin_type = None
    print(args.periodic)
    if (args.periodic == "daily"):
        checkin_type = Templates.DAILY
    elif (args.periodic == "weekly"):
        checkin_type = Templates.WEEKLY
    elif (args.periodic == "monthly"):
        checkin_type = Templates.MONTHLY
    elif (args.periodic == "yearly"):
        checkin_type = Templates.YEARLY
    else:
        print("Please pass only daily, weekly, monthly or yearly for the --periodic argument")
        assert(False)

    checkin_template = None
    checkin_template_path = os.path.join(args.template_folder, checkin_type)
    assert(os.path.exists(checkin_template_path))

    with open(checkin_template_path, "r") as f:
        checkin_template_text = f.read()
    assert(checkin_template_text)

    checkin_message = parse_template(checkin_template_text)

    subject_line = f"{args.periodic.capitalize()} Check-In {format_datetime(datetime.now())}"
    
    send_message(service, 
                 args.to_email, 
                 args.sender_email,
                 subject_line,
                 checkin_message)


