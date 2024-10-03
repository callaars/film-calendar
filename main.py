import arrow
import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import re
import os
import csv

# Cache directory for storing processed events
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

# Create region-specific directory for the calendar files
calendar_dir = 'calendars'
os.makedirs(calendar_dir, exist_ok=True)

# File to store previously processed events in the cache directory
csv_file = os.path.join(cache_dir, 'processed_events.csv')

# Ensure CSV file exists or create it
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['movie_title', 'release_date', 'region'])  # Add 'region' to CSV headers

# Function to check if an event already exists in the CSV file
def event_exists_in_csv(movie_title, release_date, region):
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['movie_title'] == movie_title and row['release_date'] == release_date and row['region'] == region:
                return True
    return False

# Function to add new event to the CSV file
def add_event_to_csv(movie_title, release_date, region):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([movie_title, release_date, region])

# Function to fetch IMDb release calendar for a specific region
def fetch_imdb_calendar(region="GB"):
    # Dynamic URL based on region
    url = f"https://www.imdb.com/calendar?region={region}"

    # Set a popular user-agent to avoid Forbidden errors
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
    }

    # Fetch the page with the custom user agent
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.content

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Region-specific calendar file
        calendar_file = os.path.join(calendar_dir, f'imdb_release_calendar_{region}.ics')

        # If the file exists, read the existing calendar, otherwise create a new one
        if os.path.exists(calendar_file):
            with open(calendar_file, 'r') as f:
                cal = Calendar(f.read())
        else:
            cal = Calendar()

        # Extract movie titles and release dates
        for div in soup.find_all('div', class_='ipc-metadata-list-summary-item__tc'):
            # Extract movie title
            title_tag = div.find('a', class_='ipc-metadata-list-summary-item__t')
            movie_title = title_tag.text.strip() if title_tag else "Untitled"

            # Extract release date (look for the parent <article> containing the date)
            article = div.find_previous('article', {'data-testid': 'calendar-section'})
            release_date = article.find('h3', class_='ipc-title__text').text.strip()

            # Convert 'Oct 04, 2024' format to 'YYYY-MM-DD' using arrow
            date_obj = arrow.get(release_date, 'MMM DD, YYYY').format('YYYY-MM-DD')

            # Check if the event already exists in the CSV file
            if not event_exists_in_csv(movie_title, date_obj, region):
                # Add new event to CSV
                add_event_to_csv(movie_title, date_obj, region)

                # Create an all-day event
                event = Event()
                event.name = movie_title
                event.begin = date_obj
                event.make_all_day()

                # Add the event to the calendar
                cal.events.add(event)

        # Save or append to the region-specific calendar file
        with open(calendar_file, 'w') as f:
            f.writelines(cal)

        print(f"Calendar for region {region} saved at {calendar_file}")
    else:
        print(f"Failed to fetch IMDb calendar for region {region}, status code: {response.status_code}")

# Fetch IMDb calendar for a specific region (e.g., 'GB' or 'US')
fetch_imdb_calendar("GB")
fetch_imdb_calendar("US")
