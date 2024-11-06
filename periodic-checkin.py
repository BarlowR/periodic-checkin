
import logging
import os
import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from gmail_tools import gmail_authenticate, send_message, search_messages, read_message


# Need all access (permission to read/send/receive emails, manage the inbox, and more)
REQUIRED_SCOPES = ['https://mail.google.com/']
TIMEFORMAT = "%y-%m-%d-%H"
TIMEZONE = timezone(-timedelta(hours=7))

class CheckInActions(Enum):
    NO_ACTION       = 0
    SEND_REMINDER   = 1
    NEW_CHECKIN     = 2

class Templates(str, Enum):
    REMINDER    = "reminder-template.md"
    YEARLY      = "yearly-template.md"
    MONTHLY     = "monthly-template.md"
    DAILY       = "daily-template.md"
    WEEKLY      = "weekly-template.md"

class Periodic:
    def __init__(self, month = "*", day_of_month = "1", week = False, day_of_week = False):
        """
        Expects cron-like syntax: asterix for all, number for one, False to ignore. 
        Ex: Every month on the first: 
            month = "*",    day_of_month = "1",     week = False, day_of_week = False
        Ex: Every day, organized by month:
            month = "*",    day_of_month = "*",     week = False, day_of_week = False
        Ex: Every week on Monday:
            month = False,  day_of_month = False,   week = "*",   day_of_week = "1"
        Ex: Every day, organized by week:
            month = False,  day_of_month = False,   week = "*",   day_of_week = "*"

        """
         # Need month for day of month to make sense
        if (day_of_month):
            assert (month)
        
        # Need week for day of week to make sense
        if (day_of_week):
            assert (week)

        # You can't combine week format and month format
        if (month or day_of_month):
            assert(not week)
            assert(not day_of_week)
        elif (week or day_of_week):
            assert(not month)
            assert(not day_of_month)

        # need one format or the other.
        assert (month or week)

        self.month = month
        self.day_of_month = day_of_month
        self.week = week
        self.day_of_week = day_of_week
        if ((day_of_month == "*") or (day_of_week == "*")):
            self.periodic_template_type = Templates.DAILY
        elif (month == "*"):
            self.periodic_template_type = Templates.MONTHLY
        elif (week == "*"):
            self.periodic_template_type = Templates.WEEKLY
        else:
            self.periodic_template_type = Templates.YEARLY

    def format_datetime(self, current_time):
        year_value = current_time.strftime("%Y")
        month_value = current_time.strftime("%m")
        day_of_month_value = current_time.strftime("%d")
        week_value = current_time.strftime("%W")
        day_of_week_value = current_time.strftime("%w")

        current_checkin = f"{year_value}-"
        for include, value in [ [self.month == "*", month_value],
                                [self.day_of_month == "*", day_of_month_value],
                                [self.week == "*", week_value],
                                [self.day_of_week == "*", day_of_week_value]]:
            if (include):
                current_checkin += f"{value}-"
        # cut off the trailing "-"
        return current_checkin[:-1]

def parse_template(template_text):
    # TODO Replace bracketed text with value
    # Ex. {month} -> November
    return template_text


class PeriodicCheckin:
    def __init__(self, 
                 gmail_service,
                 user_email = 'robbarlw@gmail.com',
                 bot_email = 'periodic.checkin@gmail.com',
                 log_file = "correspondance_log.json",
                 reminder_rate = timedelta(days=1),
                 periodic = Periodic(),
                 template_folder = "templates",
                 log_folder = "responses",
                 ):
        
        self.service = gmail_service
        self.user_email = user_email
        self.bot_email = bot_email
        self.log_file = log_file
        self.reminder_rate = reminder_rate
        self.periodic = periodic
        self.template_folder = template_folder
        self.log_folder = log_folder
        
        # Look for reminder template
        assert(os.path.isfile(os.path.join(template_folder, Templates.REMINDER)))

    def create_new_reference_id(self):
        # TODO return a pseudo-random number for identification purposes
        return 1235

    def send_reminder(self):
        reminder_template = None
        reminder_template_path = os.path.join(self.template_folder, Templates.REMINDER)
        with open(reminder_template_path, "r") as f:
            reminder_template = f.read()
        assert(reminder_template)
        reminder_message = parse_template(reminder_template)
        send_message(self.service, self.user_email, self.bot_email, "Reminder Email", reminder_message)

    def check_time_for_checkin(self, current_time):
        if not (os.path.exists(self.log_file)):
            return CheckInActions.NEW_CHECKIN
        with open(self.log_file, "r") as log_f:
            correspondance_log = json.load(log_f)
            current_checkin = self.periodic.format_datetime(current_time)

            if ((current_checkin in correspondance_log) and
                ("responded" in correspondance_log[current_checkin].keys())):
                
                if (correspondance_log[current_checkin]["responded"]):
                    return CheckInActions.NO_ACTION

                if (("latest_reminder" in correspondance_log[current_checkin].keys())):
                    last_reminder = datetime.strptime(correspondance_log[current_checkin]["latest_reminder"],
                                            TIMEFORMAT).replace(tzinfo=TIMEZONE)
                    if ((current_time - last_reminder) > self.reminder_rate):
                        return CheckInActions.SEND_REMINDER
                    return CheckInActions.NO_ACTION
            return CheckInActions.NEW_CHECKIN

    def update_correspondance_log(self, current_checkin, key, value):
        correspondance_log = {}

        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                correspondance_log = json.load(f)
            assert(correspondance_log)

        if current_checkin not in correspondance_log.keys():
            correspondance_log[current_checkin] = {}

        correspondance_log[current_checkin][key] = value
        with open(self.log_file, "w") as log_f:
            json.dump(correspondance_log, log_f)

    def new_checkin(self, current_time):
        current_checkin = self.periodic.format_datetime(current_time)
        ref_id = self.create_new_reference_id()
        self.update_correspondance_log(current_checkin, "latest_reminder", current_time.strftime(TIMEFORMAT))
        self.update_correspondance_log(current_checkin, "responded", False)
        self.update_correspondance_log(current_checkin, "reference-id", ref_id)
        checkin_template = None
        checkin_template_path = os.path.join(self.template_folder, self.periodic.periodic_template_type)
        with open(checkin_template_path, "r") as f:
            checkin_template = f.read()
        assert(checkin_template)
        checkin_message = parse_template(checkin_template)
        checkin_message += f"Ref: {ref_id}"
        send_message(self.service, 
                     self.user_email, 
                     self.bot_email,
                     f"Checkin for {current_checkin}", checkin_message)

    def check_for_response(self, current_time):
        reference = None
        with open(self.log_file, "r") as log_f:
            correspondance_log = json.load(log_f)
            current_checkin = self.periodic.format_datetime(current_time)
            if ((current_checkin in correspondance_log) and
                ("reference-id" in correspondance_log[current_checkin].keys())):
                reference = correspondance_log[current_checkin]["reference-id"]
        assert(reference)
        results = search_messages(self.service, reference)
        for result in results:
            msg = read_message(self.service, result["id"])
            if (("From" in msg.keys()) and (self.user_email in msg["From"])):
                # TODO Handle messages with chunk sizes larger than 1
                return msg["Message-Body"]["plain"][0]
        return None
    
    def save_response(self, response, current_time):
        # The True option keeps the newline character, so that when we recombine the newline is added back in
        response_lines = response.splitlines(True)
        user_message = ""

        for line in response_lines:
            if f"<{self.bot_email}>" in line:
                break
            user_message += line
        
        assert(os.path.isdir(self.log_folder))

        current_checkin = self.periodic.format_datetime(current_time)
        with open(os.path.join(self.log_folder, f"{current_checkin}.md"), "w") as f:
            f.write(user_message)

if __name__ == "__main__":
    service = gmail_authenticate(REQUIRED_SCOPES)
    current_time = datetime.now(tz=TIMEZONE)
    check_in = PeriodicCheckin(service, periodic=Periodic(month=False, day_of_month=False, week="*", day_of_week="1"))

    resp = check_in.check_for_response(current_time)
    check_in.save_response(resp, current_time)

    # if action == CheckInActions.SEND_REMINDER:
    #     send_reminder(service)
    # elif action == CheckInActions.NEW_CHECKIN:
    #     new_checkin(service, current_time)
    # else:
    #     assert(action == CheckInActions.NO_ACTION)

    # get the Gmail API service
    # send_message(service, "robbarlw@gmail.com", "periodic.checkin@gmail.com" "November Checkin", 
    # """
    # # Goals for November:

    # # Things to keep doing in November:

    # # Things to stop doing in November:

    # # How are you feeling overall?


    # Reference ID: 123456
    # """)
    


    # results = search_messages(service, "123456")
    # for result in results:
    #     msg = read_message(service, result["id"])
    #     if "<robbarlw@gmail.com>" in msg["From"]:
    #         print(msg["Message-Body"]["plain"][0])



