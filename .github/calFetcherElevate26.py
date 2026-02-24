import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import icalendar

# Base URL for Elevate Festival program
BASE_URL = "https://elevate.at/de/diskurs/programm/"
OUTPUT = "./tmp/elevate26.ics"
CET = pytz.timezone("Europe/Vienna")

BAD_STRINGS = ['–>Tickets hier erhältlich', '–> Tickets hier erhältlich']

# "Last updated" string, in CET timezone
LASTUPDATE = "Last calendar update: {}".format(datetime.now().astimezone(CET).strftime("%Y-%m-%d %H:%M:%S"))


def get_event_links():
    """Fetch listing page and extract event url + row date/time."""
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print("Failed to fetch the program page")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    event_links = []
    for row in soup.select(".table-responsive[data-date] tr"):
        event_link = row.select_one(".tagedheadline a")
        time_cell = row.select_one("td.time")
        table = row.find_parent("div", class_="table-responsive")
        date_heading = soup.select_one(f'h2[data-date="{table.get("data-date")}"]') if table else None
        if event_link:
            event_links.append({
                "url": "https://elevate.at" + event_link["href"],
                "date": date_heading.get_text(strip=True) if date_heading else None,
                "time": time_cell.get_text(" ", strip=True) if time_cell else None,
            })
    return event_links


def parse_datetime(date_text, time_text):
    """Parse date and time strings into a datetime object in CET timezone.
    Input Example:
    date_text : Mittwoch, 05 März 2025
    time_text : 19:00 - 23:00
    """
    date_text = date_text.replace("Mittwoch, ", "Wednesday, ").replace("Donnerstag, ", "Thursday, ").replace("Freitag, ", "Friday, ").replace("Samstag, ", "Saturday, ").replace("Sonntag, ", "Sunday, ").replace("März", "March")
    time_text = time_text.replace(" - ", " - ").replace(" Uhr", "")
    
    start_time, end_time = [t.strip() for t in time_text.replace("–", "-").split("-")]
    start_time = datetime.strptime(start_time, "%H:%M")
    end_time = datetime.strptime(end_time, "%H:%M")
    
    date = datetime.strptime(date_text, "%A, %d %B %Y")
    start_datetime = datetime.combine(date, start_time.time())
    end_datetime = datetime.combine(date, end_time.time())
    
    start_datetime = CET.localize(start_datetime)
    end_datetime = CET.localize(end_datetime)
    
    return start_datetime, end_datetime


def remove_bad_strings(texts):
    new_texts = []
    for text in texts:
        if text not in BAD_STRINGS:
            for bad_string in BAD_STRINGS:
                text = text.replace(bad_string, "")
            new_texts.append(text)
    return new_texts


def scrape_event_page(url, date_override=None, time_override=None):
    """Scrape individual event pages and extract metadata."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch event page: {url}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Unknown"
    subtitle = soup.find("h2", class_="subheadline").get_text(strip=True) if soup.find("h2", class_="subheadline") else None

    # Updated date extraction
    date_element = soup.select_one("div.date h2")
    date = date_override or (date_element.get_text(strip=True) if date_element else None)
    if not date:
        print(f"Warning: No date found for event {title} at {url}")

    time = time_override or (soup.find("span", class_="time").get_text(strip=True) if soup.find("span", class_="time") else None)
    location = soup.find("span", class_="location").get_text(strip=True) if soup.find("span", class_="location") else None
    
    description = [p.get_text(strip=True, separator=" ") for p in soup.select(".detail p")]
    description = "\n".join(remove_bad_strings(description)).strip()

    speakers = [s.get_text(strip=True) for s in soup.select(".detail strong")]
    speakers = remove_bad_strings(speakers)
    
    start_datetime, end_datetime = parse_datetime(date, time) if date and time else (None, None)
    
    event = {
        "title": title,
        "subtitle": subtitle,
        "date": date,
        "time": time,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "location": location,
        "description": description,
        "speakers": speakers,
        "url": url
    }
    
    return event


def event2String(event):
    for key in event:
        print("- ", key, ":", event[key])
    print("\n")


def events2Ical(events):
    """Convert a list of events into an iCal file."""
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Elevate 2026 Diskursprogramm//elevate.at//DE')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')
                 
    for event in events:
        description = ""
        if event["subtitle"]:
            description += f"{event['subtitle']}\n"
        description += f"{event['date']} {event['time']}\n\n"
        description += f"{event['description']}"
        if event["speakers"]:
            description += "\n\nSpeakers:\n" + "\n".join(event["speakers"])
        description += f"\n\nMore info: {event['url']}"
        description += f"\n\n{LASTUPDATE}"
        

        ical_event = icalendar.Event()
        ical_event.add('summary', event["title"])
        ical_event.add('description', description)
        ical_event.add('location', event["location"])
        ical_event.add('dtstart', event["start_datetime"])
        ical_event.add('dtend', event["end_datetime"])
        
        cal.add_component(ical_event)
    
    with open(OUTPUT, "wb") as f:
        f.write(cal.to_ical())


def main():
    events_list = []
    event_links = get_event_links()
    
    for link in event_links:
        event_data = scrape_event_page(link["url"], link.get("date"), link.get("time"))
        if event_data:
            events_list.append(event_data)
    
    print('Loaded events:', len(events_list))
    #print(events_list)  # Output for now, can be saved to a file
    #event2String(events_list[0])
    events2Ical(events_list)


if __name__ == "__main__":
    main()
