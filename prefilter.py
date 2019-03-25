#!/usr/bin/env python3
"""
Remove certain ships from consideration -- primarily, Them's Fighting Herds
characters.

Also, capitalize character names from their original tag form.
"""

import pickle
import re

NON_GRATA = [
    # Them's Fighting Herds.
    'applezona',
    'ariander',
    'arizona cow',
    "fightin' six",
    'fredeander',
    'oleander',
    'papreander',
    'paprihuo',
    'paprika paca',
    'paprikapie',
    'paprizona',
    'pom lamb',
    'pomeander',
    'pomshy',
    'pomzona',
    'tianander',
    'tiandash',
    'tianhuo',
    'twileander',
    'velveander',
    'velverika',
    'velvet reindeer',
    'velvezona',
    'velvity',
    # G1-exclusive character names.
    'galaxy (g1)',
    'locket (g1)',
    'firefly',
]


def titlecase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                  lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(),
                  s)


with open("data.pickle", "r+b") as f:
    ships = pickle.load(f)

extraneous = set()

# Remove non-grata characters and ships with no images at all.
for ship in ships.keys():
    for member in ship:
        if member in NON_GRATA:
            extraneous.add(ship)
    if ships[ship]['total'] == 0:
        extraneous.add(ship)

for key in extraneous:
    del ships[key]

titled_ships = {}
for ship in ships.keys():
    new_key = tuple(titlecase(x) for x in ship)
    titled_ships[new_key] = ships[ship]

with open('data-filtered.pickle', "w+b") as f:
    pickle.dump(titled_ships, f)
