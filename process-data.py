#!/usr/bin/env python3
"""
Process the raw data acquired from Derpibooru API to get the statistically
interesting bits.
"""

import arrow
import pickle

with open('raw-data.pickle', 'r+b') as f:
    data = pickle.load(f)
    ships = data['ships']
    today = data['today']

ship_statistics = dict()

for k, v in ships.items():
    stat_blob = {
        "total": len(v.keys()),
        "upvotes": 0,
        "wilson": 0,
        "date": today,
        "artists": set(),
        "artists_per_day": 0,
        "upvotes_per_day": 0,
        "wilson_per_day": 0,
        "amount_per_day": 0,
    }
    for image in v.values():
        stat_blob['upvotes'] += image.get('upvotes', 0)
        stat_blob['wilson'] += image.get('score', 0)
        stat_blob['date'] = min(stat_blob['date'],
                                arrow.get(image.get('first_seen_at',
                                                    today)).datetime)
        stat_blob['artists'] |= set(
            x for x in image.get('tags').split(', ')
            if x.startswith('artist:'))

    timespan = (today - stat_blob['date']).days
    if timespan:  # It can be zero if a shipping tag is actually empty.
        stat_blob['upvotes_per_day'] = stat_blob['upvotes'] / timespan
        stat_blob['wilson_per_day'] = stat_blob['wilson'] / timespan
        stat_blob['amount_per_day'] = stat_blob['total'] / timespan
        stat_blob['artists_per_day'] = len(stat_blob['artists']) / timespan

    ship_statistics[k] = stat_blob

with open("data.pickle", "w+b") as f:
    pickle.dump(ship_statistics, f)

print("Done!")
