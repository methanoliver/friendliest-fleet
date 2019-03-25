#!/usr/bin/env python3
"""
Build a complete shipping tag list based on Derpibooru data.
"""

import csv
import requests
import yaml
import sys
import time
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

s = requests.Session()
if config.get('proxies'):
    print("Going through proxies...")
    s.proxies.update(config['proxies'])

# Set up backoff factors and retries
retries = Retry(
    total=None,
    connect=5,
    read=5,
    status=0,
    backoff_factor=5,
    status_forcelist=[500, 502, 503, 504, 404, 403])

s.mount('https://', HTTPAdapter(max_retries=retries))

# First order of business: Get a list of all tag implications, and

url = "https://derpibooru.org/tags/implied.json"
payload = {
    "key": config.get('key'),
    "page": 1,
}

shipping_tags = dict()

while True:
    time.sleep(0.5)  # So as not to hammer Derpibooru with requests.
    r = s.get(url, params=payload)
    print("API:", r.url)
    # If the status code isn't 200, we should fail with an exception anyway...
    data = r.json()

    if not len(data):
        break

    # Data should be a list of tags.
    for tag in data:
        aliases = (tag.get('aliased_to') or '').split(', ')
        # Skip tags which are aliased to tags processed previously.
        if any([x in shipping_tags.keys() for x in aliases]):
            continue
        implied_tags = tag.get('implied_tags', '').split(', ')
        # Skip rule 63 pairings as well: They complicate things immensely.
        if "shipping" in implied_tags and "rule 63" not in implied_tags:
            print("Discovered shipping tag:", tag['name'])
            shipping_tags[tag['name']] = {
                "name": tag['name'],
                "slug": tag['slug'],
            }

    payload['page'] += 1

# Now we need to go through the shipping tags and discover
# character associations from them.

payload = {
    "key": config.get('key'),
}

tag_responses = dict()


def slugify(name):
    """
    Derpi has some special slugifying rules.
    """
    RULES = {
        ":": "-colon-",
        ".": "-dot-",
    }
    r = name
    for k, v in RULES.items():
        r = r.replace(k, v)
    return r


def investigate_tag(name):
    """
    Cache responses for individual tags, so that we don't fetch them over and
    over again.
    """
    known_data = tag_responses.get('name')
    if known_data:
        return known_data
    url = "https://derpibooru.org/tags/{}.json".format(
        slugify(potential_character_tag))
    r = s.get(url, params=payload)
    data = r.json()
    tag_data = data.get('tag', dict())
    tag_responses[name] = tag_data
    return tag_data


# Now that we have identified the tags which imply shipping, it's time
# to assign character tags to them. Unfortunately, we have to get lots and lots
# of tags to do it.
for shipping_tag_name, shipping_tag in shipping_tags.items():
    time.sleep(1)
    url = "https://derpibooru.org/tags/{}.json".format(shipping_tag['slug'])
    r = s.get(url, params=payload)
    data = r.json()

    # Weasel out the list of names of implied tags.
    implied_tags = data.get('tag', dict()).get('implied_tags', '').split(', ')

    members = set()
    for potential_character_tag in implied_tags:
        # Skip OC tags entirely. They also have special slugging rules...
        if potential_character_tag.startswith('oc:'):
            continue

        tag_data = investigate_tag(potential_character_tag)

        # We have some broken responses.
        # Those always list something more sensible in the implications, though.
        if not tag_data:
            continue

        name = tag_data.get('name')

        if tag_data.get('category', '') == "character":
            print("Character '{}' is involved in ship '{}'".format(
                name, shipping_tag_name))
            # When characters have aliases, usually, all will be present
            # in the output, but each will return a tag object with the same name.
            members.add(name)

    shipping_tag['members'] = members

# Finally, produce a CSV file in the same format as the one that
# was made manually.
with open("automated-ship-registry.csv", "w") as f:

    writer = csv.DictWriter(
        f, fieldnames=["Tag", "Aliases", "Character A", "Character B"])
    writer.writeheader()

    for shipping_tag_name, shipping_tag in shipping_tags.items():
        # Skip bogus items, like "ships" which don't have enough characters,
        # -- which would be the OC ships and other "ships" with only one character --
        # and poly pairings: they also complicate things considerably.
        # Theoretically, I *could* account for those, but I don't
        # want to rewrite the code.
        # Anyone feeling particularly up to it, pull requests welcome.

        members = list(shipping_tag['members'])
        if len(members) != 2:
            continue

        writer.writerow({
            "Tag": shipping_tag_name,
            "Aliases": "",
            "Character A": members[0],
            "Character B": members[1],
        })

print("Done!")
