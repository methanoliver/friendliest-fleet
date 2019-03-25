#!/usr/bin/env python3
"""
Using our spreadsheet of Derpibooru tag data, inquire in Derpibooru API about
the tag and image metadata and save everything we get to raw-data.pickle
"""

import csv
import requests
import yaml
import datetime
import pytz
import time
import pickle
from collections import defaultdict
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
    Lookup image metadata in Derpibooru API and return a dict of all images for
    a given tag keyed by image id.
    """

    url = "https://derpibooru.org/search.json"
    payload = {
        "key": config.get('key'),
        "perpage": 50,
        "page": 1,
        "q": tag,
    }

    all_images = dict()
    while True:
        time.sleep(0.5)  # So as not to hammer Derpibooru with requests.
        r = s.get(url, params=payload)
        print("API:", r.url)
        # If the status code isn't 200, we should fail with an exception anyway...
        data = r.json()
        images = data.get('search', [])

        for image in images:
            all_images[image['id']] = image

        # If we're past the end of the list, or this is the last page, we're done.
        if not len(images) or len(images) < 50:
            break

        payload['page'] += 1

    return all_images


ships = defaultdict(dict)
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

        # Multiple shipping tags pointing at the same pairing
        # get the image dicts they return merged.
        ships[key] = {**ships[key], **lookup_score(main_tag)}

# At this point we should have all the image metadata for every ship in memory,
# with duplicate images resulting from multiple tags pointing at the same ship
# excised.
#
# We're going to save it to process every which way later.
with open("raw-data.pickle", "w+b") as f:
    pickle.dump({'ships': ships, 'today': today}, f)

print("Done!")
