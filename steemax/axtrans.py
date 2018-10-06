#!/usr/bin/python3

import sys
import re
from dateutil.parser import parse
from datetime import datetime
from steemax import axdb
from steemax import axverify
from steemax import default
from steemax import sec
from screenlogger.screenlogger import Msg
from simplesteem.simplesteem import SimpleSteem


class MemoMsg:
    def __init__(self):
        self.db = axdb.AXdb(default.dbuser,
                            default.dbpass,
                            default.dbname)
        self.reaction = None
        self.returnmsg = None
        self.memoid = None
        self.action = None
        self.percentage = None
        self.ratio = None
        self.duration = None
        self.sendto = None

    def invite_msg(self, acct1, acct2,
                   memoid):
        """ Creates the invite message
        """
        self.reaction = "started"
        self.db.update_status(0, memoid)
        invite = self.db.get_invite(memoid)
        msg = ("Hello @{}, @{} has invited you "
               + " to an auto-upvote exchange. "
               + "They have offered {}% of their upvote "
               + "At a ratio of {}:1 for {} days. "
               ).format(acct2, acct1,
                        invite[0], invite[1], invite[2])
        # Verify the user has an account. If they do,
        # send them the memo id code
        if self.db.get_user_token(acct2):
            msg += ("Please send any amount SBD to "
                    + "@steem-ax with the following in "
                    + "the memo: '{}:accept'. ").format(memoid)
        # Otherwise we skip that part of the message. 
        msg += ("For more info please visit "
                + "https://steemax.info/@{}").format(acct2)
        self.returnmsg = msg

    def accepted_msg(self, acct, memoid):
        """ Creates the accept message 
        """
        self.reaction = "accepted"
        self.db.update_status(1, memoid)
        self.returnmsg = (
            "@{} has accepted the invite. ".format(acct)
            + "The auto-upvote exchange will "
            + "begin immediately.")

    def barter_msg(self, reaction, status, acct,
                   per, ratio, dur, memoid, acct2):
        """ Creates the barter message
        """
        self.reaction = reaction
        # We must choose the proper pronun because the percentage
        # is always taken from the inviter's (not invitee) upvote 
        if status == 2:
            pronoun = "their"
        else:
            pronoun = "your"
        # ADd the new values to the database
        self.db.update_invite(per, ratio,
                              dur, memoid, status)
        self.returnmsg = (
            ("@{} has offered to barter. They offer "
             + "{}% of {} upvote at a ratio of "
             + "{}:1 for {} days. "
             + "Send any SBD along with this "
             + "memo code to @steem-ax to accept this invite: "
             + "\n\n'{}:accept'. "
             + "To generate your own barter offer, "
             + "please visit https://steemax.info/@{}").format(
                acct, per, pronoun, ratio, dur, memoid, acct2))

    def ignore(self, reason):
        """ Creates the ignore message 
        """
        self.reaction = "refund"
        self.returnmsg = reason

    def cancel(self, canceller, memoid, rstatus):
        """ The cancel command can be 
        given at any time by either party
        """
        if int(rstatus) == 4:
            self.ignore("The exchange has already been canceled.")
        else:
            self.reaction = "cancelled"
            self.db.update_status(4, memoid)
            self.returnmsg = ("@" + canceller
                              + " has cancelled the exchange.")


class Reaction(MemoMsg):
    def start(self, acct1, acct2, memofrom,
              rstatus, memoid):
        """ The start method grants the authority to the 
        exchange from the inviter. 
        """
        # Only the inviter can start the exchange
        if acct1 == memofrom:
            # if the rstatus is -1 then the exchange invite has been
            # created in the database but not yet sent to the invitee.
            if rstatus < 0:
                self.invite_msg(acct1, acct2, memoid)
            else:
                self.ignore("@{} has already".format(acct1)
                            + "started this exchange.")
        # If the invitee sent the memo we tell them to wait.
        elif acct2 == memofrom:
            self.ignore("Invalid action. @{} ".format(acct1)
                        + " has not yet started this "
                        + "exchange.")
        # If it's neither party the memo is invalid.
        else:
            self.ignore("Invalid Memo ID.")

    def accept(self, acct1, acct2, memofrom,
               rstatus, memoid):
        """ The accept method is used to authorize 
        a change whenever an invite or a barter is 
        sent. 
        """
        # The memo is from the inviter
        if acct1 == memofrom:
            # The invite is pending
            # on the inviter to accept a barter
            if int(rstatus) == 3:
                # The accept message is sent
                self.accepted_msg(acct1, memoid)
            else:
                self.ignore("Invalid command.")
        # The memo is from the invitee
        elif acct2 == memofrom:
            # The invite has been initially sent
            # (rstatus = 0) or the invite is pending on the
            # invitee to accept a barter (rstatus = 2)
            if int(rstatus) == 0 or int(rstatus) == 2:
                # The accept message is sent
                self.accepted_msg(acct2, memoid)
            else:
                self.ignore("Invalid command.")
        # If the memo is from neither party it is invalid.              
        else:
            self.ignore("Invalid Memo ID.")

    def barter(self, acct1, acct2, memoid, memofrom,
               rstatus, per, ratio, dur):
        """ A barter command can be used any 
        time after both parties have authorized 
        the exchange.
         2 = inviter (account1) has offered to barter
         3 = invitee (account2) has offered to barter
        When a user enter values from the web interface
        the javascript corrects most errors. Here we
        catch errors if the user has decided to create
        their own memo id commands to send directly from
        their wallet and has made a mistake.
        """
        invalid = False
        verify = axverify.AXverify()
        # First we verify that the percentage and ratio
        # create a valid exchange. There are some instances
        # where the values entered, even when within the correct
        # limits, are not possible. This is partly due to vote weight
        # not being alloed to be lower than 1%
        if not verify.eligible_votes(
                acct1, acct2, per, ratio, 1):
            # The eligible_votes method returns an explanation
            # for why the ratio and percentage were invalid
            # usually because the ratio is too high or low
            self.ignore("Barter invalid. " + verify.response)
            return
        # The memo is from the inviter
        if acct1 == memofrom:
            # The invitee has sent a barter offer.
            if int(rstatus) == 3:
                # A barter offer is sent in return
                # to the invitee's barter offer
                self.barter_msg("acct1 bartering", 2,
                                acct1, per, ratio,
                                dur, memoid, acct2)
            else:
                invalid = True
        # The memo is from the invitee
        elif acct2 == memofrom:
            # The invite has been initially sent
            # (rstatus = 0) or the invite is pending on the
            # invitee to accept a barter (rstatus = 2)
            if int(rstatus) == 0 or int(rstatus) == 2:
                # a barter offer is sent in return
                self.barter_msg("acct2 bartering", 3,
                                acct2, per, ratio,
                                dur, memoid, acct1)
            else:
                invalid = True
        # The memo id matches neither party
        else:
            self.ignore("Invalid Memo ID.")
        # The barter offer was sent by the wrong party.
        if invalid:
            self.ignore("Invalid barter. Please be sure that @"
                        + acct1 + " has started the invite. "
                        + "If you've already sent a barter "
                        + "please wait for the other side to "
                        + "respond.")


class AXtrans:
    def __init__(self):
        self.msg = Msg(default.logfilename,
                       default.logpath,
                       default.msgmode)
        self.db = axdb.AXdb(default.dbuser,
                            default.dbpass,
                            default.dbname)
        self.steem = SimpleSteem()
        self.react = Reaction()
        self.memoid = ""
        self.action = ""
        self.percentage = ""
        self.ratio = ""
        self.duration = ""
        self.sendto = ""

    def parse_memo(self, **kwargs):
        """ Parses the memo message in a transaction
        for the appropriate action.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        try:
            memo = self.memo.split(":")
        # A broad exception is used because any exception
        # should return false.
        except:
            return False
        # Everything from the outside world is 
        # filtered for security
        self.memoid = sec.filter_token(memo[0])
        if len(memo) == 2:
            self.action = sec.filter_account(memo[1])
            return True
        elif len(memo) == 5:
            self.action = sec.filter_account(memo[1])
            self.percentage = sec.filter_number(memo[2])
            self.ratio = sec.filter_number(memo[3], 1000)
            self.duration = sec.filter_number(memo[4], 365)
            return True
        else:
            return False

    def send(self, to="artopium",
             amt="0.001 SBD",
             msg="test"):
        """ Sends the forwarded amount of SBD along
        with the reaction message
        """
        # Split "SBD" from the amount
        r = amt.split(" ")
        # Actually transfer it
        if self.steem.transfer_funds(to, float(r[0]),
                                     r[1], msg):
            self.msg.message(("Transaction committed. Sent {} "
                              "{} to {} with the memo: "
                              "{}").format(r[0], r[1], to, msg))

    def act(self, acct1, acct2, rstatus, sendto):
        """ Decides how to react baed on the action
        present in the memo message
        """
        if not self.db.get_user_token(self.memofrom):
            self.react.ignore(
                ("@{} is not a current member of "
                 + " https://steemax.trade !!Join now!! "
                 + "using SteemConnect.").format(self.memofrom))
        elif self.action == "start":
            self.react.start(acct1,
                             acct2,
                             self.memofrom,
                             rstatus,
                             self.memoid)
        elif self.action == "cancel":
            self.react.cancel(self.memofrom, self.memoid, rstatus)
        elif self.action == "accept":
            self.react.accept(acct1, acct2, self.memofrom, rstatus, self.memoid)
        elif self.action == "barter":
            self.react.barter(acct1, acct2, self.memoid, self.memofrom, rstatus,
                              self.percentage, self.ratio, self.duration)
        else:
            self.react.ignore("Invalid action.")
        if self.react.reaction == "refund":
            self.sendto = self.memofrom
        else:
            self.sendto = sendto

    def parse_history_record(self, record, lasttrans):
        """ Parses the blockchain record for transdactions
        sent to @steem-ax 
        """
        if (record[1]['op'][0] == 'transfer'
            and datetime.strptime(
                record[1]['timestamp'],
                '%Y-%m-%dT%H:%M:%S')
                > lasttrans
            and re.match(r'^[0-9]{32}',
                         record[1]['op'][1]['memo'])
            and record[1]['op'][1]['to']
                == self.steem.mainaccount):
            return True
        else:
            return False

    def fetch_history(self):
        """ Processes the transaction history. 
        The memo message is parsed for a valid 
        command and performs the 
        directed action.
        """
        rt = self.db.get_most_recent_trans()
        for a in self.steem.get_my_history():
            if self.parse_history_record(a, rt):
                if self.parse_memo(memofrom=a[1]['op'][1]['from'],
                                   memo=a[1]['op'][1]['memo'],
                                   amount=a[1]['op'][1]['amount'],
                                   trxid=a[1]['trx_id'],
                                   txtime=a[1]['timestamp']):
                    if self.db.verify_memoid(self.memofrom, self.memoid):
                        self.act(self.db.dbresults[0][0],
                                 self.db.dbresults[0][1],
                                 int(self.db.dbresults[0][2]),
                                 self.db.sendto)
                    else:
                        self.react.ignore("Invalid Memo ID.")
                        self.sendto = self.memofrom
                else:
                    self.react.ignore("Invalid Memo.")
                    self.sendto = self.memofrom
                self.send(self.sendto,
                          self.amount,
                          self.react.returnmsg)
                self.db.add_trans(self.trxid,
                                  self.memofrom,
                                  self.amount,
                                  self.memoid,
                                  self.react.reaction,
                                  self.txtime)

# EOF
