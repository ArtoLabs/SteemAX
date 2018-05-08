#!/usr/bin/python3

from steem import Steem
from steem.converter import Converter
import re

nodes = [
    'https://steemd.minnowsupportproject.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com',
    'https://steemd.steemgigs.org'
]

s = Steem(nodes)

h = s.get_account_history("artturtle", -1, 200)

for a in h:

    if a[1]['op'][0] == 'transfer':

        if a[1]['op'][1]['to'] == 'artturtle' and re.match(r'^\s*[0-9]{32}[\:]*.*$', a[1]['op'][1]['memo']):

            print (a[1]['op'][1]['amount'] + " from " + a[1]['op'][1]['from'] + "\n   Memo: " + a[1]['op'][1]['memo'])


