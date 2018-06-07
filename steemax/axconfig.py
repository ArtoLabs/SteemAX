#!/usr/bin/python3

class Config:

    def __init__(self):
        self.mainaccount = "steem-ax"
        self.post_max_days_old = 5
        self.dbusername = "steemax"
        self.dbname = "steemax"
        self.dbpass = "SteemAX_pass23"

        self.nodes = ['https://steemd.minnowsupportproject.org',
            'https://steemd.privex.io',
            'https://gtg.steem.house:8090',
            'https://steemd.pevo.science',
            'https://rpc.steemliberator.com']

        self.keys = []

