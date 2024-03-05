import requests
import time
import urllib.parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import pandas as pd
from selenium import webdriver  # Importing Selenium's webdriver module
# Assume 'cards' is an array of card objects

# Define a class to represent a card object
class Card:
    def __init__(self, job_id, job_title, job_date, job_loc, job_summary, job_salary, job_url, company_name):
        self.job_id = job_id
        self.job_title = job_title
        self.job_date = job_date
        self.job_loc = job_loc
        self.job_summary = job_summary
        self.job_salary = job_salary
        self.job_url = job_url
        self.company_name = company_name



source = "indeed.com"



def get_url(position):
    """
    Generate URL from position
    """
    encoded_position = urllib.parse.quote(position)
    return f"https://indeed.com/jobs?q={encoded_position}"


def get_job_date(card):
    """
    Extracts date from the job post record
    """
    post_str = card.find('span', {'class': 'date'}).text
    post_days = re.findall(r'\d+', post_str)

    if post_days:
        job_date = (datetime.now() - timedelta(days=int(post_days[0]))).strftime("%d/%m/%Y")
    else:
        job_date = datetime.now().strftime("%d/%m/%Y")

    return job_date

def get_job_salaries(card):
    """
    Extracts salaries
    """
    try:
        salary_str = card.find('div', 'metadata salary-snippet-container').text
        salaries = re.findall(r"\b(\w+[.]\w+)", salary_str)
    except AttributeError:
        salaries = []

    return salaries

def get_record(card):
    """
    Extract job data from a single record
    """
    try:
        job_id = card.get("data-jk")
        job_title_element = card.span
        print("Job Title Element:", job_title_element)  # Debug print
        job_title = job_title_element.get("title").strip() if job_title_element and job_title_element.get("title") else 'N/A'
        job_url = 'https://www.indeed.com' + card.get('href') if card.get('href') else 'N/A'
        company_name_element = card.find('span', {'class': 'companyName'})
        print("Company Name Element:", company_name_element)  # Debug print
        company_name = company_name_element.text.strip() if company_name_element and company_name_element.text else 'N/A'
        job_loc_element = card.find('div', {'class': 'companyLocation'})
        print("Job Location Element:", job_loc_element)  # Debug print
        job_loc = job_loc_element.text.strip() if job_loc_element and job_loc_element.text else 'N/A'
        job_summary_element = card.find('div', {'class': 'job-snippet'})
        print("Job Summary Element:", job_summary_element)  # Debug print
        job_summary = job_summary_element.text.strip() if job_summary_element and job_summary_element.text else 'N/A'
        job_date = get_job_date(card)
        job_salary = get_job_salaries(card)

        # Replace None values with a default value (e.g., 'N/A')
        job_id = job_id if job_id is not None else 'N/A'
        job_date = job_date if job_date is not None else 'N/A'
        job_salary = job_salary if job_salary is not None else 'N/A'

        record = (job_id, job_title, job_date, job_loc, job_summary, job_salary, job_url, company_name)
        return record

    except Exception as e:
        print(f"An error occurred in get_record: {e}")
        return None






def get_jobs(position):
    """
    Creates a DataFrame with all records (scraped jobs), scraping from all pages
    """
    url = get_url(position)
    records = []
    session = requests.Session()
    page = 1

    # Configuring Selenium to use the Chromium driver from the downloads folder
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=C:\\Users\\christofer p\\Downloads")  # Adjust the path accordingly
    driver = webdriver.Chrome(options=options)  # Using the specified options

    while True:
        try:
            driver.get(url)
            print(f"Navigating to URL: {url}")
            time.sleep(3)  # Let the page load
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.find_all('div', 'job_seen_beacon')
            print(f"Number of job cards found: {len(cards)}")

            if not cards:
                print("No job cards found. Exiting.")
                break

            for card in cards:
                record = get_record(card)
                if record is not None:  # Check if record is not None before appending
                    print("Record:", record)  # Print out the retrieved record
                    records.append(record)
                else:
                    print("Skipping None record.")

            next_page_link = soup.find('a', {'aria-label': 'Next'})
            if not next_page_link:
                print("No next page link found. Exiting.")
                break

            url = 'https://indeed.com/' + next_page_link.get('href')
            page += 1

        except Exception as e:
            print(f"An error occurred: {e}")
            break

    driver.quit()  # Quit the Selenium driver

    columns = ['job_id', 'job_title', 'job_date', 'job_loc', 'job_summary', 'job_salary', 'job_url', 'company_name']
    df = pd.DataFrame(data=records, columns=columns)

    search_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    df["search_time"] = search_time
    df["search_position"] = position
    df["source"] = source

    return df



