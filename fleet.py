#!/usr/bin/env python3
"""
Using the data.pickle prepared by fetch-data.py, compute the Friendliest Fleet
based on it.

I recommend you run this as 'nice ./fleet.py' just in case.
"""

import operator
import networkx as nx
import dwave_networkx as dnx
import neal
import pickle

# The scoring parameter we're using.
# You can use:
# 'upvotes_per_day',
# 'wilson_per_day', -- I'm not sure it makes *sense* to do this to a Wilson score,
# 'amount_per_day', -- The number of images per day.
#
# "per day" means simply "from the earliest posted image in the ship to today."
SCORE_KEY = 'upvotes_per_day'

# Cutoff value for ships: Ships with fewer total images are not considered
# for the calculation.
COUNT_CUTOFF = 50

# Number of times to run the optimizer.
# Only the highest scoring result will be reported.
LOOPS = 500

with open("data-filtered.pickle", "r+b") as f:
    ships = pickle.load(f)

G = nx.Graph()

# Pre-filter the ships for cutoff.
inconsequential = set()
for ship in ships.keys():
    if ships[ship]['total'] < COUNT_CUTOFF:
        inconsequential.add(ship)

for ship in inconsequential:
    del ships[ship]

print("\nPairings detected:")
for ship in ships.keys():
    G.add_node(ship, weight=ships[ship][SCORE_KEY])
    print("{}/{}: {}".format(ship[0], ship[1], ships[ship][SCORE_KEY]))

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
for i in range(LOOPS):
    version = dnx.maximum_weighted_independent_set(G, weight='weight')
    score = sum([ships[ship][SCORE_KEY] for ship in version])
    print(score)
    if score > highest_score:
        highest_score = score
        highest = version

fleet = {ship: ships[ship][SCORE_KEY] for ship in highest}

print("\n```\nHighest scoring fleet:\n")
for ship in sorted(fleet.items(), key=operator.itemgetter(1), reverse=True):
    ship, score = ship
    print("{:<9.4f} - {} / {}".format(score, ship[0], ship[1]))

print("\nTotal fleet score:", highest_score)
print("```")
