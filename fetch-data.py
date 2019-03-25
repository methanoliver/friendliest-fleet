#!/usr/bin/env python3
"""
Using our spreadsheet of Derpibooru tag data, inquire in Derpibooru
API about tag and image metadata and save the results to data.pickle,
precomputing some values.
"""

import csv
import requests
import yaml
import json
import sys
import datetime
import pytz
import sys
import time
import arrow
import pickle
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

s = requests.Session()
if config.get('proxies'):
    print("Going through proxies...")
    s.proxies.update(config['proxies'])

# Set up backoff factors and retries: I've had a round of data collection
# that got aborted because the API was a bit flaky and didn't respond.
retries = Retry(
    total=5,
    connect=5,
    read=5,
    status=0,
    backoff_factor=5,
    status_forcelist=[500, 502, 503, 504, 404, 403])

s.mount('https://', HTTPAdapter(max_retries=retries))


def lookup_score(tag):
    """
    Lookup image metadata in Derpibooru API and compute scores a given tag
    has.  This is done by simply requesting the entirety of the image search
    for this tag, and going through all the image information packets returned
    until they are exhausted.
    """

    url = "https://derpibooru.org/search.json"
    payload = {
        "key": config.get('key'),
        "perpage": 50,
        "page": 1,
        "q": tag,
    }

    total = 0
    upvotes = 0
    wilson = 0
    date = today
    while True:
        time.sleep(0.5)  # So as not to hammer Derpibooru with requests.
        r = s.get(url, params=payload)
        print("API:", r.url)
        # If the status code isn't 200, we should fail with an exception anyway...
        data = r.json()
        total = max(total, data.get('total', 0))
        images = data.get('search', [])
        # If we're past the end of the list, we're done.
        if not len(images):
            break
        for image in data.get('search', []):
            upvotes += image.get('upvotes')
            wilson += image.get('score')
            image_date = image.get('first_seen_at')
            if image_date:
                date = min(date, arrow.get(image_date).datetime)
        # If we're on the last page, we don't have to fetch again
        # to be sure we are.
        if len(images) < 50:
            break
        payload['page'] += 1

    return upvotes, wilson, date, total


ships = dict()
tags = set()
names = set()

today = datetime.datetime.now(tz=pytz.utc)

# Sanity checking stage:
# We're working starting with a list of tags and the characters paired in them
# from a CSV file, which was written by manually investigating the tags.
# As such, it can contain typos, which were a problem at some point.

with open('automated-ship-registry.csv', "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        char_a = row['Character A'].strip()
        char_b = row['Character B'].strip()
        names.add(char_a)
        names.add(char_b)

# Print every name encountered to catch typos here.
print("Distinct names:")
for x in sorted(names):
    print(x)

# Now actually proceeding with the API requests.
with open('automated-ship-registry.csv', "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Avoid duplicates in case any are left in the initial data.
        main_tag = row['Tag'].strip()
        taglist = [main_tag] + row['Aliases'].split()
        if any([x in tags for x in taglist]):
            tags |= set(taglist)
            continue
        tags |= set(taglist)
        char_a = row['Character A'].strip()
        char_b = row['Character B'].strip()
        key = tuple(sorted([char_a, char_b]))

        ship_data = ships.get(key, {
            "upvotes": 0,
            "wilson": 0,
            "date": today,
            "total": 0,
        })

        upvotes, wilson, date, total, = lookup_score(main_tag)
        ship_data['upvotes'] += upvotes
        ship_data['wilson'] += wilson
        ship_data['date'] = min(ship_data['date'], date)
        ship_data['total'] += total

        ships[key] = ship_data

for k, v in ships.items():
    timespan = (today - v['date']).days
    if timespan:  # It can be zero if a shipping tag is actually empty.
        v['upvotes_per_day'] = v['upvotes'] / timespan
        v['wilson_per_day'] = v['wilson'] / timespan
        v['amount_per_day'] = v['total'] / timespan
    else:
        v['upvotes_per_day'] = 0
        v['wilson_per_day'] = 0
        v['amount_per_day'] = 0

with open("data.pickle", "w+b") as f:
    pickle.dump(ships, f)

print("Done!")
