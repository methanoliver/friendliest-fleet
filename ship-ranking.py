#!/usr/bin/env python3
"""
Using the data.pickle prepared by fetch-data.py, print out a table ranking
current ship popularity, as well as make a CSV file.
"""

import pickle
import operator
import csv

SCORE_KEY = 'upvotes_per_day'

with open("data-filtered.pickle", "r+b") as f:
    ships = pickle.load(f)

print("```")

with open("time-weighted-ranking.csv", "w") as f:
    writer = csv.DictWriter(f, [
        "Character A",
        "Character B",
        "Image count",
        "Earliest appearance",
        "Total upvotes",
        "Upvotes per day",
        "Total Wilson score",
        "Wilson per day",
        "Images per day",
    ])
    writer.writeheader()
    for ship in sorted(
            ships.items(), key=lambda x: x[1][SCORE_KEY], reverse=True):
        ship, data = ship
        if data[SCORE_KEY] > 1.0:
            print("{:<9.4f} - {} / {}".format(data[SCORE_KEY], ship[0],
                                              ship[1]))
        writer.writerow({
            "Character A": ship[0],
            "Character B": ship[1],
            "Image count": data['total'],
            "Earliest appearance": data['date'],
            "Total upvotes": data.get('upvotes', 0),
            "Upvotes per day": data.get('upvotes_per_day', 0),
            "Total Wilson score": data.get('wilson', 0),
            "Wilson per day": data.get('wilson_per_day', 0),
            "Images per day": data.get('amount_per_day', 0),
        })

print("```")
