#!/usr/bin/python3

from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem
from steemax import default
from steemax import axdb


class AXverify:
    def __init__(self):
        self.steem = SimpleSteem(client_id=default.client_id,
                                 client_secret=default.client_secret,
                                 callback_url=default.callback_url,
                                 screenmode=default.msgmode)
        self.msg = Msg(default.logfilename,
                       default.logpath,
                       default.msgmode)
        self.response = None
        self.post_one = ""
        self.post_two = ""
        self.vote_cut = 0
        self.post_list = {}

    def vote_on_it(self, voter, author, post, weight):
        """ Use the tokens in the database to vote on
        a post. If the vote fails, renews the token
        and tries again.
        """
        db = axdb.AXdb(default.dbuser,
                       default.dbpass,
                       default.dbname)
        if db.get_user_token(voter) is not False:
            accesstoken = db.dbresults[0][1]
            refreshtoken = db.dbresults[0][2]
        else:
            return False
        # If the vote fails then we renew the token
        if not self.sc_vote(voter, author, post, weight, accesstoken):
            print("Renewing token for " + voter)
            newtoken = self.renew_token(voter, refreshtoken)
            if newtoken is not False:
                return self.sc_vote(voter, author, post, weight, newtoken)
            else:
                self.msg.error_message("A NEW TOKEN COULD NOT BE CREATED")
                return False

    def sc_vote(self, voter, author, post, weight, token):
        """ Takes the given token and initializes SteemConnect
        to make a vote. Analyzes the result and prints the
        outcome to screen as well as returns a boolean result.
        """
        self.steem.connect.sc = None
        self.steem.connect.steemconnect(
            token)
        result = self.steem.connect.vote(
            voter,
            author,
            post,
            int(weight))
        try:
            result['error']
        # We use a broad exception clause to "catch" everything
        # that is not an error
        except:
            # The vote was successful
            print(str(voter) + " has voted on "
                  + str(post) + " "
                  + str(weight) + "%")
            return True
        else:
            self.msg.error_message(str(result))
            return False

    def renew_token(self, accountname, refreshtoken):
        """ If the access token has expired
        use the refresh token to get a new accss token.
        """
        if self.steem.verify_key(
                acctname="", tokenkey=refreshtoken):
            db = axdb.AXdb(default.dbuser,
                           default.dbpass,
                           default.dbname)
            db.update_token(self.steem.username,
                            self.steem.accesstoken,
                            self.steem.refreshtoken)
            return self.steem.accesstoken
        else:
            return False

    def get_vote_value(self, acctname, voteweight=100,
                       votepower=0):
        """ Voteweight and votepower are entered 
        as a percentage value (1 to 100)
        If the default is used for votepower (0) 
        it is set by the system at the time
        the account last voted.
        """
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

    def verify_post(self, account1, account2):
        """ Gets only the most recent post, gets the 
        timestamp and finds the age of the post in days.
        Is the post too old? Did account2 
        vote on the post already?
        """
        from_memory = False
        if account1 in self.post_list:
            identifier = self.post_list[account1]["id"]
            from_memory = True
        else:
            identifier = self.steem.recent_post(account1, 0, 1)
            self.post_list[account1] = {"id":identifier,"votes":None}
        if identifier is False or identifier is None:
            self.msg.message("No post for " + account1)
            return False
        else:
            permlink = self.steem.util.permlink(identifier)
            if from_memory:
                votes = self.post_list[account1]["votes"]
            else:
                votes = self.steem.vote_history(permlink[1], account1)
                self.post_list[account1]["votes"] = votes
            if votes is not None and len(votes) > 0:
                for v in votes:
                    if v['voter'] == account2:
                        self.msg.message(account2 +
                                       " has already voted on " + permlink[1])
                        return False
        return permlink[1]

    def eligible_posts(self, account1, account2):
        """ Verify the posts of both accounts
        """

        post = self.verify_post(account1, account2)

        if post is False or post is None:
            self.msg.message(account1
                             + " does not have an eligible post.")
            return False
        else:
            self.post_one = post
        post = self.verify_post(account2, account1)
        if post is False or post is None:
            self.msg.message(account2
                             + " does not have an eligible post.")
            return False
        else:
            self.post_two = post
        return True

    def eligible_votes(self, account1, account2,
                       percentage, ratio, flag):
        """ If the flag is raised use the full voting 
        power to make the comparison rather
        than the current voting power. 
        If ratio was not acheived return false 
        Otherwise display approximate 
        upvote matches
        """
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
        self.vote_cut = v3
        v4 = self.get_vote_value(account2, v3, vpow)
        v1s = self.steem.rshares_to_steem(v1)
        v4s = self.steem.rshares_to_steem(v4)
        if exceeds and flag != 2:
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
