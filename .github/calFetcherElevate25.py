import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Base URL for Elevate Festival program
BASE_URL = "https://elevate.at/de/diskurs/programm/"
CET = pytz.timezone("Europe/Berlin")

def get_event_links():
    """Fetch the event listing page and extract individual event links."""
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print("Failed to fetch the program page")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    event_links = ["https://elevate.at" + event['href'] for event in soup.select(".tagedheadline a")]
    return event_links

def parse_datetime(date_text, time_text):
    """Parse date and time strings into a datetime object in CET timezone."""
    try:
        start_time, end_time = time_text.split(" - ")
        date_time_start = datetime.strptime(f"{date_text} {start_time}", "%d. %B %Y %H:%M")
        date_time_end = datetime.strptime(f"{date_text} {end_time}", "%d. %B %Y %H:%M")
        return CET.localize(date_time_start), CET.localize(date_time_end)
    except Exception as e:
        print(f"Error parsing datetime: {e}")
        return None, None

def scrape_event_page(url):
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
    date = date_element.get_text(strip=True) if date_element else None
    if not date:
        print(f"Warning: No date found for event {title} at {url}")

    time = soup.find("span", class_="time").get_text(strip=True) if soup.find("span", class_="time") else None
    location = soup.find("span", class_="location").get_text(strip=True) if soup.find("span", class_="location") else None
    description = " ".join([p.get_text(strip=True) for p in soup.select(".detail p")])
    speakers = [s.get_text(strip=True) for s in soup.select(".detail strong")]
    
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
        "speakers": speakers
    }
    
    return event



def main():
    events_list = []
    event_links = get_event_links()
    
    for link in event_links:
        event_data = scrape_event_page(link)
        if event_data:
            events_list.append(event_data)
        break
    
    print('Loaded events:', len(events_list))
    #print(events_list)  # Output for now, can be saved to a file
    print(events_list[0])


if __name__ == "__main__":
    main()
