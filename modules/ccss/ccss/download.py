'''This is a script which downloads CCSS standards.

This script is a one-off, since it will break if the page layout ever
changes. It was half-generated by GPT. The core of this package are
the JSON files extracted, and the scripts to make use of them.
'''

from bs4 import BeautifulSoup
import requests
import json

# Fetch the webpage
subjects = ["ELA-Literacy", "Math"]


def fetch_urls(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    nav = soup.find('div', {'id': 'sidebar'})
    all_urls = [a['href'] for a in nav.find_all('a')]
    return [
        u.replace('../', '')
        for u in all_urls
        if 'pdf' not in u and 'http' not in u
    ]


def fetch_standards(url):
    response = requests.get(url)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the standards and sub-standards
    standards = soup.find_all('div', {'class': 'standard'})
    standards_json = {}
    for standard in standards:
        identifier = standard.find('a', {'class': 'identifier'}).text
        description = standard.find('br').next_sibling
        standards_json[identifier] = description.strip()

    # Find the substandards
    substandards = soup.find_all('div', {'class': 'substandard'})
    substandards_json = {}
    for substandard in substandards:
        identifier = substandard.find('a', {'class': 'identifier'}).text
        description = substandard.find('br').next_sibling
        substandards_json[identifier] = description.strip()

    # Output the JSON document
    return standards_json, substandards_json


all_standards = {}

for subject in subjects:
    base_url = f"https://www.thecorestandards.org/{subject}"
    for u in fetch_urls(base_url):
        try:
            standards, substandards = fetch_standards(
                f"https://www.thecorestandards.org/{u}")
            all_standards.update(standards)
            all_standards.update(substandards)
        except Exception:
            print(f"Skipping {u}")

print(json.dumps(all_standards, indent=2))

json.dump(all_standards, open("ccss.json", "w"), indent=2)
