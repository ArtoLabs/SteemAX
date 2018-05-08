#!/usr/bin/python3

import axdb
import axverify

xdb = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
xverify = axverify.AXverify()

def x_run_exchanges(mode):
    xresults = xdb.get_axlist(mode)
    for row in xresults:
        idk = row[0]
        acct1 = row[1]
        acct2 = row[2]
        key1 = row[3]
        key2 = row[4]
        per = row[5]
        ratio = row[6]
        dur = row[7]
        memoid = row[8]
        status = row[9]
        time = row[10]
        if xverify.x_eligible_posts (acct1, acct2, mode):
            if xverify.x_eligible_votes (acct1, acct2, per, ratio, mode, 0):
                print ("\nAuto exchange occured.\n")
