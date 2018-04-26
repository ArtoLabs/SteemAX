#!/usr/bin/python

from dateutil.parser import parse
from datetime import datetime
from steem import Steem
from steem.converter import Converter
from steem.amount import Amount
from steembase.account import PrivateKey
from steembase.exceptions import InvalidWifError
import steemax.axdb

nodes = [
    'https://steemd.minnowsupportproject.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com',
    'https://steemd.steemgigs.org'
]

s = Steem(nodes)
c = Converter()


def x_get_steemit_balances(mode):

    results = steemax.axdb.x_fetch_reward_fund(mode)

    if steemax.axdb.x_check_reward_fund_renewal(results[3]):    

        # Get and the current Steemit reward fund steem-python object used to retreive the following values

        reward_fund = s.get_reward_fund()

        # The current Steemit reward balance (reward pool)

        reward_balance = Amount(reward_fund["reward_balance"]).amount

        # The recent claims made on the reward balance (upvotes for the day subtracting from the reward pool)

        recent_claims = float(reward_fund["recent_claims"])
        
        # The price of Steem in USD

        base = Amount(s.get_current_median_history_price()["base"]).amount

        # Save to database

        steemax.axdb.x_save_reward_fund(reward_balance, recent_claims, base, mode)

        # Print to screen

        if mode == "verbose":
            print ("\n------------------------------------------------")
            print ("   Reward balance: " + str(reward_balance))
            print ("   Recent claims: " + str(recent_claims))
            print ("   Steem = $" + str(base))
            print ("------------------------------------------------\n")

        return [reward_balance, recent_claims, base]
    
    else:

        if mode == "verbose":
            print ("\n------------------------------------------------")
            print ("   Reward balance: " + str(results[0]))
            print ("   Recent claims: " + str(results[1]))
            print ("   Steem = $" + str(results[0]))
            print ("------------------------------------------------\n")

        return [results[0], results[1], results[2]]


def x_verify_key (acctname, private_posting_key, mode):

    # Verify a Steemit Private Posting Key    
    
    pubkey = 0
    acct = ""

    # Get a new instance of the Steemd node with the key to be tested

    try:
        steem = Steem(nodes, keys=[private_posting_key])
    except InvalidWifError as e:
        if mode != "quiet":
            print("Invalid key: " + str(e))
        return False

    # Convert the Private Posting Key into the Public Posting Key

    try:
        pubkey = PrivateKey(private_posting_key).pubkey
    except:
        if mode != "quiet":
            print ("Bad private key")
        return False

    # Get the account for which the key is to be tested against

    try:
        acct = steem.get_account(acctname)
    except:
        if mode != "quiet":
            print ("Could not connect to steemd")
        return False

    # Compare the Public Posting Keys with each other

    if acct:
        pubkey2 = acct['posting']['key_auths'][0][0]
    if str(pubkey) != str(pubkey2):
        if mode != "quiet":
            print ("The private key and account name provided do not match.")
        return False
    else:
        if mode != "quiet":
            print ("Private key is valid.")
        return True


def get_vote_value (acctname, weight, power, mode):

    # voteweight and votepower are entered as a percentage value (1 to 100)
    # but the steem python library needs these values to be in the range of 150 to 10000

    voteweight = int(weight) * 100
    if voteweight < 150:
        voteweight = 150
    if voteweight > 10000:
        voteweight = 10000

    votepower = power * 100
    if votepower > 0:
        if votepower < 150:
            votepower = 150
        elif votepower > 10000:
            votepower = 10000

    # Get the account

    try:
        acct = s.get_account(acctname)
    except:
        if mode != "quiet":
            print ("Could not connect to steemd")
        return False

    if not acct:
        print ("Could not find account: " + acctname)
        return False

    # The value returned by 'voting_power' is set by the system at the time
    # the account last voted. How long it's been since the last vote?

    vp = acct['voting_power']
    lvt = acct['last_vote_time']
    vs = acct['vesting_shares']

    # Remove the word VESTS from delegation results

    a = vs.split(" ")
    vs = a[0]
    dvests = acct['delegated_vesting_shares']
    a = dvests.split(" ")
    dvests = a[0]
    rvests = acct['received_vesting_shares']
    a = rvests.split(" ")
    rvests = a[0]

    # Find Vests after delegations

    vests = (float(vs) - float(dvests)) + float(rvests) 

    # Convert vests to Steem Power

    sp = c.vests_to_sp(vests)


    # If provided, use the manually entered value for vote power

    if votepower > 0:
        vpow_scaled = votepower
        vpow = power

    # Otherwise calculate vote power at present moment

    else:

        # Convert timestamp to number of seconds since right now

        delta = datetime.utcnow() - datetime.strptime(lvt,'%Y-%m-%dT%H:%M:%S')
        td = delta.days
        ts = delta.seconds
        tt = (td * 86400) + ts

        # Calculate true voting power since last vote in range of 150 to 10000

        regenerated_vp = tt * 10000 / 86400 / 5
        vpow_scaled = vp + regenerated_vp

        # Convert range to normal percentage for printing to screen

        vpow = vpow_scaled / 100
        vpow = round(vpow, 2)

        if vpow > 100:
            vpow = 100

    # Convert to rshares

    rshares = c.sp_to_rshares(sp, vpow_scaled, voteweight)

    if mode == "verbose":

        # Convert rshares to Steem
        sb = x_get_steemit_balances(mode)
        votevalue = rshares * sb[0] / sb[1] * sb[2]
        votevalue = round(votevalue, 4)

        print ("\n__" + acctname + "__\n   Vote Power: " + str(vpow) + 
            "%\n   Steem Power: " + str(sp) + "\n   Vote Value at " + str(weight) + "%: $" + str(votevalue) + "\n");

    return rshares


def verify_post (account1, account2, mode):

    now = datetime.now()

    # Get only the most recent post

    try:
        p = s.get_blog(account1, 0, 1)
    except:
        if mode != "quiet":
            print ("Could not connect to steemd")
        return False

    if not p:
        if mode != "quiet":
            print ("Could not find a blog post for " + account1)
        return False

    # Get the timestamp and find age of post in days

    created = p[0]['comment']['created']
    t = datetime.strptime(created,'%Y-%m-%dT%H:%M:%S')
    delta = now - t
    td = delta.days

    # Is the post too old?

    if td > 5:
        if mode != "quiet":
            print ("@" + account1 + "/" + p[0]['comment']['permlink'] + " is more than 5 days old.")
        return False

    # Did account2 vote on the post already?

    votes = s.get_active_votes(p[0]['comment']['author'], p[0]['comment']['permlink'])
    for v in votes:
        if v['voter'] == account2:
            if mode != "quiet":
                print (account2 + " has aready voted on " + p[0]['comment']['permlink'])
            return False

    return True


def x_eligible_posts (account1, account2, mode):

    # Verify the posts of both accounts

    if not verify_post(account1, account2, mode):
        return False
    if not verify_post(account2, account1, mode):
        return False

    return True


def x_eligible_votes (account1, account2, percentage, ratio, mode, flag):

    # If the flag is raised use the full voting power to make the comparison rather
    # than the current voting power. Full voting power is used to make the ratio comparison
    # at the time the invite is created and during the barter process. Current voting power
    # is used at the time of the actual exchange

    if flag == 1:
        vpow = 100
    else:
        vpow = 0

    # Verify that the upvote exchange will be equal

    exceeds = False
    
    v1 = get_vote_value(account1, percentage, vpow, mode)
    if not v1:
        return False
    v2 = get_vote_value(account2, 100, vpow, mode)
    if not v2:
        return False

    # Determine how much (percentage) of account2's upvote is needed to match account1

    v3 = ((v1 / v2) * 100) / float(ratio)
    v3a = round(v3, 2)

    # Calculate better ratio if there is one

    r = float(ratio) / (1 / v3)
    newratio = float(ratio) * r
    newratio = round(newratio, 2)

    # If the ratio cannot be acheived then 'exceeds' is true

    if v3a < 1:
        v3 = 1
        exceeds = True

    if v3a > 100:
        v3 = 100
        exceeds = True

    if mode != "quiet":

        print (account2 + " needs to vote " + str(v3a) + "% in order to meet " + account1)
    
    # Get the new vote value from account2 at the adjusted percentage
    
    v4 = get_vote_value(account2, v3, vpow, mode)

    # Convert rshares to steem

    sb = x_get_steemit_balances(mode)

    v1s = v1 * sb[0] / sb[1] * sb[2] 
    v4s = v4 * sb[0] / sb[1] * sb[2]
    v1s = round(v1s, 4)
    v4s = round(v4s, 4)

    # If ratio was not acheived return false and suggest a new ratio

    if exceeds:
        if v3 == 1:
            v5 = v4 - v1
            v5s = v5 * sb[0] / sb[1] * sb[2]
            if mode != "quiet":
                print (account2 + "'s vote of " + str(v4s) + " will be larger than " + account1 + "'s vote by: " + str(v5s))
        if v3 == 100:
            v5 = v1 - v4
            v5s = v5 * sb[0] / sb[1] * sb[2]
            if mode != "quiet":
                print (account1 + "'s vote of " + str(v1s) + " will be larger than " + account2 + "'s vote by: " + str(v5s))
        if mode != "quiet":
            print ("Perhaps try a new ratio of " + str(newratio) + " to 1")
        return False

    # Otherwise display approximate upvote matches and return true

    else:

        if mode != "quiet":
            print (account1 + " will upvote $" + str(v1s) + " and " + account2 + " will upvote $" + str(v4s));
        
        return True


# Run as main

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 4:
        print ("Please enter two account names and a percentage to find eligibility.")
        sys.exit()

    acct1 = str(sys.argv[1])
    acct2 = str(sys.argv[2])
    per = int(sys.argv[3])

    if len(sys.argv) == 5:
        md = str(sys.argv[4])
    else:
        md = ""

    xe = x_eligible(acct1, acct2, per, md)

    print ("Match eligible: " + str(xe))


# EOF

