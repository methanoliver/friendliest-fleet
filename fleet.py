#!/usr/bin/env python3

import csv
from collections import defaultdict
import operator
import networkx as nx
import dwave_networkx as dnx
import neal

ships = defaultdict(int)
tags = set()
names = set()

with open('Most Satisfactory Fleet - Sheet1.csv', "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Avoid duplicates in case any are left in the initial data.
        taglist = [row['Tag'].strip()] + row['Aliases'].split()
        if any([x in tags for x in taglist]):
            tags |= set(taglist)
            continue
        tags |= set(taglist)

        char_a = row['Character A'].strip()
        char_b = row['Character B'].strip()
        names.add(char_a)
        names.add(char_b)
        ships[tuple(sorted([char_a, char_b]))] += int(row['Score'])

# To make it easier to sort out typos.
print("Distinct names:")
for x in sorted(names):
    print(x)

# Ignore low-scoring pairings.
too_low = []
for ship, score in ships.items():
    if score <= 100:
        too_low.append(ship)
for ship in too_low:
    del ships[ship]

G = nx.Graph()

print("\nPairings detected:")
for ship in ships.keys():

    G.add_node(ship, weight=ships[ship])
    print("{}/{}: {}".format(ship[0], ship[1], ships[ship]))

print("Total pairings:", nx.number_of_nodes(G), end="\n\n")

for ship in ships.keys():
    for partner in ship:
        for potential_link in ships.keys():
            if ship == potential_link:
                continue
            if partner in potential_link:
                G.add_edge(ship, potential_link)

sm = neal.SimulatedAnnealingSampler()
dnx.set_default_sampler(sm)

highest = None
highest_score = 0

print("\nSearching for solutions...")
for i in range(1, 500):
    version = dnx.maximum_weighted_independent_set(G, weight='weight')
    score = sum([ships[ship] for ship in version])
    print(score)
    if score > highest_score:
        highest_score = score
        highest = version

fleet = {ship: ships[ship] for ship in highest}

print("\n```\nHighest scoring fleet:")
for ship in sorted(fleet.items(), key=operator.itemgetter(1), reverse=True):
    ship, score = ship
    print("{0: <4} - {1} / {2}".format(score, ship[0], ship[1]))

print("\nTotal fleet score:", highest_score)
print("```")
