#!/usr/bin/python

from dateutil.parser import parse
from datetime import datetime
from steem import Steem
from steem.converter import Converter
from steem.amount import Amount
from steembase.account import PrivateKey
from steembase.exceptions import InvalidWifError
import axdb

nodes = [
    'https://steemd.minnowsupportproject.org',
    'https://steemd.privex.io',
    'https://steemd.steemit.com',
    'https://steemd.steemgigs.org'
]

s = Steem(nodes)
c = Converter()
adb = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")

class AXverify:

 
    def x_print_steemit_balances(self):
        print ("\n------------------------------------------------")
        print ("   Reward balance: " + str(self.reward_balance))
        print ("   Recent claims: " + str(self.recent_claims))
        print ("   Steem = $" + str(self.base))
        print ("------------------------------------------------\n")
 

    def x_get_steemit_balances(self):
        '''Get and the current Steemit reward fund steem-python object used to retreive the following values
                The current Steemit reward balance (reward pool)
                The recent claims made on the reward balance (upvotes for the day subtracting from the reward pool)
                The price of Steem in USD
        '''
        adb.x_fetch_reward_fund()
        if adb.x_check_reward_fund_renewal():    
            reward_fund = s.get_reward_fund()
            self.reward_balance = Amount(reward_fund["reward_balance"]).amount
            self.recent_claims = float(reward_fund["recent_claims"])
            self.base = Amount(s.get_current_median_history_price()["base"]).amount
            adb.x_save_reward_fund(self.reward_balance, self.recent_claims, self.base)
        else:
            self.reward_balance = adb.results[0]
            self.recent_claims = adb.results[1]
            self.base = adb.results[2]
        self.x_print_steemit_balances()


    def x_verify_key (self, acctname, private_posting_key, mode):

        ''' Get a new instance of the Steemd node and verify a Steemit Private Posting Key
            by first converting the Private Posting Key into the Public Posting Key
            then get the account for which the key is to be tested against then
            compare the Public Posting Keys with each other.
        '''
        pubkey = 0
        acct = ""
        try:
            steem = Steem(nodes, keys=[private_posting_key])
        except InvalidWifError as e:
            if mode != "quiet":
                print("Invalid key: " + str(e))
            return False
        try:
            pubkey = PrivateKey(private_posting_key).pubkey
        except:
            if mode != "quiet":
                print ("Bad private key")
            return False
        try:
            acct = steem.get_account(acctname)
        except:
            if mode != "quiet":
                print ("Could not connect to steemd")
            return False
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


    def get_vote_value (self, acctname, weight, power, mode):
        ''' Voteweight and votepower are entered as a percentage value (1 to 100)
        but the steem python library needs these values to be in the range of 150 to 10000.
        The value returned by 'voting_power' is set by the system at the time
        the account last voted. How long it's been since the last vote?
        Calculate true voting power since last vote in range of 150 to 10000.
        Convert to rshares and STEEEM.
        '''
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
        try:
            acct = s.get_account(acctname)
        except:
            if mode != "quiet":
                print ("Could not connect to steemd")
            return False
        if not acct:
            print ("Could not find account: " + acctname)
            return False
        vp = acct['voting_power']
        lvt = acct['last_vote_time']
        vs = Amount(acct['vesting_shares']).amount
        dvests = Amount(acct['delegated_vesting_shares']).amount
        rvests = Amount(acct['received_vesting_shares']).amount
        vests = (float(vs) - float(dvests)) + float(rvests) 
        sp = c.vests_to_sp(vests)
        if votepower > 0:
            vpow_scaled = votepower
            vpow = power
        else:
            delta = datetime.utcnow() - datetime.strptime(lvt,'%Y-%m-%dT%H:%M:%S')
            td = delta.days
            ts = delta.seconds
            tt = (td * 86400) + ts
            # time since last vote * sp_to_rshares range * seconds in a day * days it takes to regenerate
            regenerated_vp = tt * 10000 / 86400 / 5
            vpow_scaled = vp + regenerated_vp
            # If more time has passed then is needed to reach 100% then we are just at 100%
            if vpow_scaled > 10000:
                vpow_scaled = 10000
            # We hand vpow_scaled to sp_to_rshares and vpow to the screen
            vpow = vpow_scaled / 100
            vpow = round(vpow, 2)
        rshares = c.sp_to_rshares(sp, vpow_scaled, voteweight)
        if mode == "verbose":
            x_get_steemit_balances()
            votevalue = rshares * self.reward_balance / self.recent_claims * self.base
            votevalue = round(votevalue, 4)
            print ("\n__" + acctname + "__\n   Vote Power: " + str(vpow) + 
                "%\n   Steem Power: " + str(sp) + "\n   Vote Value at " + str(weight) + "%: $" + str(votevalue) + "\n");
        return rshares


    def verify_post (self, account1, account2, mode):
        ''' Gets only the most recent post, gets the timestamp and finds the age of the post in days.
        Is the post too old? Did account2 vote on the post already?

        '''
        now = datetime.now()
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
        created = p[0]['comment']['created']
        t = datetime.strptime(created,'%Y-%m-%dT%H:%M:%S')
        delta = now - t
        td = delta.days
        if td > 5:
            if mode != "quiet":
                print ("@" + account1 + "/" + p[0]['comment']['permlink'] + " is more than 5 days old.")
            return False
        votes = s.get_active_votes(p[0]['comment']['author'], p[0]['comment']['permlink'])
        for v in votes:
            if v['voter'] == account2:
                if mode != "quiet":
                    print (account2 + " has aready voted on " + p[0]['comment']['permlink'])
                return False
        return True


    def x_eligible_posts (self, account1, account2, mode):
        ''' Verify the posts of both accounts
        '''
        if not verify_post(account1, account2, mode):
            return False
        if not verify_post(account2, account1, mode):
            return False
        return True


    def x_eligible_votes (self, account1, account2, percentage, ratio, mode, flag):
        ''' If the flag is raised use the full voting power to make the comparison rather
        than the current voting power. Full voting power is used to make the ratio comparison
        at the time the invite is created and during the barter process. Current voting power
        is used at the time of the actual exchange. Verify that the upvote exchange will be equal.
        Determine how much (percentage) of account2's upvote is needed to match account1.
        Calculate better ratio if there is one. If the ratio cannot be acheived then 'exceeds' is true.
        Get the new vote value from account2 at the adjusted percentage. Convert rshares to steem.
        If ratio was not acheived return false and suggest a new ratio. Otherwise display approximate 
        upvote matches and return true.
        '''
        if flag == 1:
            vpow = 100
        else:
            vpow = 0
        exceeds = False
        # If vpow is zero get_vote_value uses the value returned from steemd instead
        v1 = self.get_vote_value(account1, percentage, vpow, mode)
        if not v1:
            return False
        v2 = self.get_vote_value(account2, 100, vpow, mode)
        if not v2:
            return False
        v3 = ((v1 / v2) * 100) / float(ratio)
        v3a = round(v3, 2)
        r = float(ratio) / (1 / v3)
        newratio = float(ratio) * r
        newratio = round(newratio, 2)
        if v3a < 1:
            v3 = 1
            exceeds = True
        if v3a > 100:
            v3 = 100
            exceeds = True
        if mode != "quiet":
            print (account2 + " needs to vote " + str(v3a) + "% in order to meet " + account1)
        v4 = self.get_vote_value(account2, v3, vpow, mode)
        self.x_get_steemit_balances()
        v1s = v1 * self.reward_balance / self.recent_claims * self.base 
        v4s = v4 * self.reward_balance / self.recent_claims * self.base
        v1s = round(v1s, 4)
        v4s = round(v4s, 4)
        if exceeds:
            if v3 == 1:
                v5 = v4 - v1
                v5s = v5 * self.reward_balance / self.recent_claims * self.base
                if mode != "quiet":
                    print (account2 + "'s vote of " + str(v4s) + " will be larger than " + account1 + "'s vote by: " + str(v5s))
            if v3 == 100:
                v5 = v1 - v4
                v5s = v5 * self.reward_balance / self.recent_claims * self.base
                if mode != "quiet":
                    print (account1 + "'s vote of " + str(v1s) + " will be larger than " + account2 + "'s vote by: " + str(v5s))
            if mode != "quiet":
                print ("Perhaps try a new ratio of " + str(newratio) + " to 1")
            return False
        else:
            if mode != "quiet":
                print (account1 + " will upvote $" + str(v1s) + " and " + account2 + " will upvote $" + str(v4s));
            return True


# Run as main

if __name__ == "__main__":

    import sys

    a = AXverify()

    if len(sys.argv) < 4:
        print ("Please enter two account names and a percentage to find eligibility.")
    else:
        acct1 = str(sys.argv[1])
        acct2 = str(sys.argv[2])
        per = int(sys.argv[3])

        xe = a.x_eligible_votes(acct1, acct2, per, 1, "", "")
        print ("Match eligible: " + str(xe))


# EOF

