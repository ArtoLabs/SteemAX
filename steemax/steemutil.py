#!/usr/bin/python3

import time
import re
from datetime import datetime
from steemax import axmsg
from steemax import axconfig
from steem import Steem
from steem.post import Post
from steem.amount import Amount
from steem.converter import Converter
from steembase.account import PrivateKey

import urllib.request
from urllib.error import HTTPError



class Utilities:  



    def __init__(self):

        self.cfg = axconfig.Config()

        self.msg = axmsg.AXmsg()

        self.s = None

        self.c = None



    def identifier(self, author, permlink):

        return ("@" + author + "/" + permlink)



    def days_back(self, date):

        return (datetime.now() - datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')).days



    def goodnode(self, nodelist):

        for n in nodelist:

            req = urllib.request.Request(url=n)

            try:
                self.msg.message("Trying " + n)
                urllib.request.urlopen(req)

            except HTTPError as e:
                self.msg.error_message(e)

                return False

            else:
                self.msg.message("Using " + n)

                return n



    def steem_instance(self):

        if self.s:
            return self.s

        for x in range(3):

            try:
                self.s = Steem(keys=self.cfg.keys, nodes=[self.goodnode(self.cfg.nodes)])

            except Exception as e:
                self.msg.error_message("COULD NOT GET STEEM INSTANCE")
                self.msg.error_message(e)
                self.msg.error_message("will try again in 60 seconds")
                
                time.sleep(60)

            else:
                return self.s

        return None




    def claim_rewards(self):

        try:
            self.steem_instance().claim_reward_balance(account=self.cfg.mainaccount)

        except Exception as e:
            self.msg.error_message(e)

        else:
            self.msg.message("Rewards have been claimed")

            time.sleep(10)



    def verify_key (self, acctname, private_posting_key):
        ''' Get a new instance of the Steemd node and verify a Steemit Private Posting Key
            by first converting the Private Posting Key into the Public Posting Key
            then get the account for which the key is to be tested against then
            compare the Public Posting Keys with each other.
        '''

        pubkey = PrivateKey(private_posting_key).pubkey or 0
        pubkey2 = self.steem_instance().get_account(acctname)['posting']['key_auths'][0][0]

        if str(pubkey) != str(pubkey2):
            xmsg.error_message("The private key and account name provided do not match.")
            return False

        else:
            xmsg.message("Private key is valid.")
            return True



    def reward_pool_balances(self):
        '''Get and the current Steemit reward fund steem-python object used to retreive the following values
                The current Steemit reward balance (reward pool)
                The recent claims made on the reward balance (upvotes for the day subtracting from the reward pool)
                The price of Steem in USD
        '''

        reward_fund = self.steem_instance().get_reward_fund()

        self.reward_balance = Amount(reward_fund["reward_balance"]).amount
        self.recent_claims = float(reward_fund["recent_claims"])
        self.base = Amount(self.steem_instance().get_current_median_history_price()["base"]).amount

        return [self.reward_balance, self.recent_claims, self.base]


    
    def scale_vote(self, value):

        value = int(value) * 100

        if value < 150:
            value = 150
        if value > 10000:
            value = 10000

        return value



    def rshares_to_steem (self, rshares):

        self.reward_pool_balances()

        return round(rshares * self.reward_balance / self.recent_claims * self.base, 4)



    def current_vote_value(self, voteweight=100, votepower=0, lastvotetime=None, steempower=0):

        c = Converter()

        voteweight = self.scale_vote(voteweight)

        if votepower > 0:
            self.votepower = self.scale_vote(votepower) 

        else:
            delta = datetime.utcnow() - datetime.strptime(lastvotetime,'%Y-%m-%dT%H:%M:%S')
            td = delta.days
            ts = delta.seconds
            tt = (td * 86400) + ts
            regenerated_vp = tt * 10000 / 86400 / 5

            votepower = self.scale_vote(self.votepower + regenerated_vp)

            self.votepower = round(votepower / 100, 2)

        self.rshares = c.sp_to_rshares(steempower, votepower, voteweight)

        return self.rshares_to_steem(self.rshares)



    def check_balances(self, account):

        c = Converter()

        try:
            acct = self.steem_instance().get_account(account)

        except Exception as e:
            self.msg.error_message(e)
            return False

        else:
            self.sbdbal = Amount(acct['sbd_balance']).amount or 0
            self.steembal = Amount(acct['balance']).amount or 0

            self.votepower = acct['voting_power']
            self.lastvotetime = acct['last_vote_time']

            vs = Amount(acct['vesting_shares']).amount
            dvests = Amount(acct['delegated_vesting_shares']).amount
            rvests = Amount(acct['received_vesting_shares']).amount

            vests = (float(vs) - float(dvests)) + float(rvests) 

            self.steempower = c.vests_to_sp(vests) or 0

            time.sleep(5)

            return [self.sbdbal, self.steembal, self.steempower, self.votepower, self.lastvotetime]



    def transfer_funds(self, to, amount, denom, msg):

        try:
            self.steem_instance().commit.transfer(to, float(amount), denom, msg, self.cfg.mainaccount)

        except Exception as e:
            self.msg.error_message(e)
            return False

        else:
            return True



    def get_my_history(self, account=None, limit=100):

        if not account:
            account = self.cfg.mainaccount

        try:
            h = self.steem_instance().get_account_history(account, -1, limit)

        except Exception as e:
            self.msg.error_message(e)
            return False

        else:

            time.sleep(5)

            return h



    def post_to_blog(self, title, body, permlink, tags):

        for num_of_retries in range(4):

            self.msg.message("Attempting to post blog.")

            try:
                self.steem_instance().post(title, body, self.cfg.mainaccount, permlink, None, None, None, None, tags, None, True)   

            except Exception as e:
                self.msg.error_message("COULD NOT POST '" + title + "'")
                self.msg.error_message(e)
                self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 10 seconds.")

                time.sleep(10)

            else:
                self.msg.message("Waiting 2 minutes for the broadcast to take effect.")

                time.sleep(5)

                self.msg.message("Checking to see if post is in the blockchain.")

                checkident = self.get_post_info(self.cfg.mainaccount)

                self.msg.message("The identifier found is " + checkident)

                ident = self.identifier(self.cfg.mainaccount, permlink)

                self.msg.message("Which will be checked against " + ident)

                if checkident == ident:
                    return True

                else:
                    self.msg.error_message("A POST JUST CREATED WAS NOT FOUND IN THE BLOCKCHAIN '" + title + "'")
                    self.msg.error_message(e)
                    self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 10 seconds.")

                    time.sleep(10)



    def reply_to_post(self, permlink, msgbody):

        for num_of_retries in range(4): 

            try:
                self.steem_instance().post("hello", msgbody, self.cfg.mainaccount, None, permlink, None, None, "", None, None, False)

            except Exception as e:
                self.msg.error_message("COULD NOT REPLY TO " + permlink)
                self.msg.error_message(e)
                self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 30 seconds.")

                time.sleep(30)

            else:
                self.msg.message("Replied to " + permlink)

                time.sleep(30)

                return True



    def unfollowing(self, author):

        try:
            self.steem_instance().commit.unfollow(author, ['blog'], self.cfg.mainaccount)

        except Exception as e:
            self.msg.error_message(e)
            return False

        else:
            return True



    def who_im_following(self, account):

        following = []

        try:
            temp = self.steem_instance().get_following(account, '', 'blog', 100)
            
        except Exception as e:
            self.msg.error_message(e)
            return False

        else:
            for a in temp:
                following.append(a['following'])

            return following



    def get_post_info(self, author, daysback=0):

        for num_of_retries in range(4):

            try:
                blog = self.steem_instance().get_blog(author, 0, 30)

            except Exception as e:
                self.msg.error_message("COULD NOT GET THE MOST RECENT POST FOR " + author)
                self.msg.error_message(e)
                self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 10 seconds.")

                time.sleep(10)

            else:
                if daysback > 0:

                    for p in blog:

                        if p['comment']['author'] == author and self.days_back(p['comment']['created']) == daysback:

                            return self.identifier(p['comment']['author'], p['comment']['permlink'])

                else:
                    if blog[0]['comment']['author'] == author and not self.days_back(blog[0]['comment']['created']) > self.cfg.post_max_days_old:

                        self.post_max_days_old = self.cfg.post_max_days_old
                
                        return self.identifier(blog[0]['comment']['author'], blog[0]['comment']['permlink'])

                    else:
                        return False



    def get_vote_history(self, author, permlink):

        return self.steem_instance().get_active_votes(author, permlink)



    def vote_on_it(self, identifier):

        for num_of_retries in range(4):

            try:
                self.steem_instance().vote(identifier, 100.0, self.cfg.mainaccount)

                self.msg.message("voting for " + identifier)

                time.sleep(10)

            except Exception as e:

                self.msg.error_message("COULD NOT VOTE ON " + identifier)

                if re.search(r'You have already voted in a similar way', str(e)):

                    self.msg.error_message("Already voted on " + identifier)

                    return "already voted"

                else:
                    self.msg.error_message(e)

                self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 10 seconds.")

                time.sleep(10)

                return False

            else:
                return True



    def resteem_it(self, identifier):

        for num_of_retries in range(4):

            try:
                self.steem_instance().resteem(identifier, self.cfg.mainaccount)

                self.msg.message("resteemed " + identifier)

                time.sleep(30)

            except Exception as e:
                self.msg.error_message("COULD NOT RESTEEM " + identifier)
                self.msg.error_message(e)
                self.msg.error_message("Attempt number " + str(num_of_retries) + ". Retrying in 10 seconds.")

                time.sleep(10)

                return False

            else:
                return True



# Run as main

if __name__ == "__main__":

   
    u = Utilities("artopium")
    print (u.get_post_info("artopium", 3))




# EOF
