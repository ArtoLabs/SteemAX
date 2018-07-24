#!/usr/bin/python3

from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem
from steemax import default


class AXverify:


    def __init__(self):
        self.msg = Msg(default.logfilename, 
                        default.logpath,
                        default.msgmode)
        self.steem = SimpleSteem(client_id=default.client_id,
                                client_secret=default.client_secret,
                                callback_url=default.callback_url,
                                screenmode=default.msgmode)
        self.response = None


    def get_vote_value (self, acctname, voteweight=100, 
                        votepower=0):
        ''' Voteweight and votepower are entered 
        as a percentage value (1 to 100)
        If the default is used for votepower (0) 
        it is set by the system at the time
        the account last voted.
        '''
        self.steem.check_balances(acctname)
        if votepower == 0:
            votepower = self.steem.votepower
        self.votevalue = self.steem.current_vote_value(
                    lastvotetime=self.steem.lastvotetime, 
                    steempower=self.steem.steempower, 
                    voteweight=int(voteweight), 
                    votepower=int(votepower))
        self.voteweight = voteweight
        self.votepower = votepower
        return self.steem.rshares


    def verify_post (self, account1, account2, mode):
        ''' Gets only the most recent post, gets the 
        timestamp and finds the age of the post in days.
        Is the post too old? Did account2 
        vote on the post already?
        '''
        permlink = self.steem.get_post_info(account1)
        if not permlink:
            self.msg.error_message("No post for " + account1)
            return False
        else:
            votes = self.steem.vote_history(account1, permlink)
            for v in votes:
                if v['voter'] == account2:
                    self.msg.message(account2 + 
                        " has aready voted on " + permlink)
                    return False
        return True


    def eligible_posts (self, account1, account2, mode):
        ''' Verify the posts of both accounts
        '''
        if not self.verify_post(account1, account2, mode):
            return False
        if not self.verify_post(account2, account1, mode):
            return False
        return True


    def eligible_votes (self, account1, account2, 
                        percentage, ratio, mode, flag):
        ''' If the flag is raised use the full voting 
        power to make the comparison rather
        than the current voting power. 
        If ratio was not acheived return false 
        Otherwise display approximate 
        upvote matches
        '''
        if flag == 1:
            vpow = 100
        else:
            vpow = 0
        v1 = self.get_vote_value(account1, percentage, vpow)
        v2 = self.get_vote_value(account2, 100, vpow)
        v3 = ((v1 / v2) * 100) / float(ratio)
        v3a = round(v3, 2)
        exceeds = False
        if v3a < 1:
            v3 = 1
            exceeds = True
        if v3a > 100:
            v3 = 100
            exceeds = True
        self.msg.message(account2 + " needs to vote " 
                + str(v3a) + "% in order to meet " + account1)
        trythis = v3 * 100
        v4 = self.get_vote_value(account2, trythis, vpow)
        
        v1s = self.steem.rshares_to_steem(v1)
        v4s = self.steem.rshares_to_steem(v4)
        if exceeds:
            if v3 == 1:
                v5 = v4 - v1
                v5s = self.steem.rshares_to_steem(v5)
                self.response = (account2 + "'s vote of " + str(v4s) 
                                + " will be larger than " + account1 
                                + "'s vote by: " + str(v5s))
                self.msg.message(self.response)
            if v3 == 100:
                v5 = v1 - v4
                v5s = self.steem.rshares_to_steem(v5)
                self.response = (account1 + "'s vote of " + str(v1s) 
                                + " will be larger than " + account2 
                                + "'s vote by: " + str(v5s))
                self.msg.message(self.response)
            return False
        else:
            self.msg.message(account1 + " will upvote $" + str(v1s) 
                    + " and " + account2 + " will upvote $" + str(v4s))
            return True


# EOF
