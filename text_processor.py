from datetime import datetime
import re

def process_text(text):
    current_time = datetime.now()
    text = re.sub("{year}", current_time.strftime("%Y"), text)
    text = re.sub("{month}", current_time.strftime("%B"), text)
    text = re.sub("{month_number}", current_time.strftime("%m"), text)
    text = re.sub("{day_of_month}", current_time.strftime("%d"), text)
    text = re.sub("{week}", current_time.strftime("%W"), text)
    text = re.sub("{day_of_week}", current_time.strftime("%w"), text)

    return text

if __name__ == "__main__":
    print(process_text("{year}-{month_number}-{day_of_month}"))
