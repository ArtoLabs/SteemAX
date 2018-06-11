#!/usr/bin/python3

from cmd import Cmd
from steemax import axe
from steemax import axdb
from steemax import axverify
from steemax import axtrans
from screenlogger.screenlogger import Msg
import re
import sys


msg = Msg()
db = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
xverify = axverify.AXverify()


def enter_account_name(flag, mode):
    ''' Prompt user for their Steemit account name. 
    'flag' indicates entering the account name 
    for an invitee or inviter
    '''
    if flag:
        question = 'Your account name @'
    else:
        question = 'Their account name @'
    while True:
        acct = input(question)
        if not re.match( r'^[a-z0-9\-]+$', acct) or len(acct) == 0 or len(acct) > 32:
            msg.message("The account name you entered is "
                        + "blank or contains invalid characters.")
        else:
            if xverify.get_vote_value(acct, 100, 0, mode):
                break
    return acct


def enter_memo_id(acct):
    ''' Prompt user for the unique Memo ID that 
    was generated during the creation of an invite
    '''
    while True:
        memoid = input('Memo ID: ')
        if not re.match( r'^[0-9]+$', memoid) or len(memoid) == 0 or len(memoid) > 32:
            msg.message("The Memo ID you entered is "
                        + "blank or contains invalid characters.")
        else:
            if db.verify_memoid(acct, memoid):
                break
    return memoid


def enter_percentage(acct):
    ''' Prompt user for the percentage of their 
    upvote they wish to exchange. 
    This is always a percentage of the inviter's 
    (Account1) upvote, not the invitee (Account2)
    '''
    while True:
        per = input("Percentage of " + acct + "'s upvote (1 to 100): ")
        if not re.match( r'^[0-9]+$', per) or len(per) == 0 or len(per) > 3 or int(per) < 1 or int(per) > 100:
            msg.message("Please only enter a number between 1 and 100.")
        else:
            break
    return per


def enter_ratio(acct1, acct2, per, flag):
    ''' Prompt user for the ratio between accounts for the exchanges. This ratios is expressed as a two digit decimal number
    to two places in proportion to 1, i.e. XX.xx to 1. e.g. 0.01 to 1, 10.10 to 1, 1.25 to 1, etc.
    This is always so that X is inviter's (Account1) upvote, to 1 which is the invitee's (Account2) upvote
    '''
    while True:
        ratio = input('Ratio between upvotes. Enter as X ('+acct1+') to 1 ('+acct2+'). X is: ')
        if not re.match( r'^[0-9\.]+$', ratio) or len(ratio) == 0 or len(ratio) > 5 or float(ratio) < 0.01 or float(ratio) > 99:
            msg.message("Please enter a one or two digit number to represent a ratio in the format x to 1 where x is your input. Enter a decimal to two places to represent a ratio less than one. e.g. 0.05 to 1")
        else:
            if xverify.eligible_votes(acct1, acct2, per, ratio, "", flag):
                break
    return ratio


def enter_duration():
    ''' Promt user to enter the duration of the auto exchange in the number of days
    '''
    while True:
        dur = input('Duration of exchange in days: ')
        if not re.match( r'[0-9]', dur) or len(dur) == 0 or len(dur) > 3:
            msg.message("Please only enter a number up to three digits.")
        else:
            break
    return dur


def enter_key(acct):
    ''' Prompt user for their private posting key as found in their steemit.com wallet
    '''
    while True:
        key = input('Your Private Posting Key: ')
        if not re.match( r'^[A-Za-z0-9]+$', key) or len(key) == 0 or len(key) > 64:
            msg.message("The private posting key you entered is blank or contains invalid characters.")
        else:
            if xverify.verify_key(acct, key, ""):
                break
    return key


# Command shell


def run(args=None):

    db.first_time_setup()
    prompt = MyPrompt()
    prompt.prompt = '[steemax]# '
    prompt.cmdloop('\n   ** Welcome to SteemAX ** \n')


class MyPrompt(Cmd):
    ''' Command line interface for SteemAX
    '''


    def do_run(self, args):
        axe.run_exchanges("")


    def do_process(self, args):
        xtrans = axtrans.AXtrans()
        xtrans.fetch_history()


    def do_invite(self, args):
        ''' Start an auto-upvote exchange between two Steemit accounts 
        '''
        acct1 = enter_account_name(1, "verbose")
        acct2 = enter_account_name(0, "verbose")
        key = enter_key(acct1)
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 1)
        dur = enter_duration()
        memoid = db.add_invite (acct1, acct2, key, per, ratio, dur)
        if memoid:
            msg.message("An invite has been created. To authorize this exchange and to send the invite please send any amount of SBD to @steem-ax along with the following memo message. Your SBD will be forwarded to the invitee:\n\n   " + memoid + ":start\n")
        else:
            msg.message("An invite could not be created.")


    def do_accept(self, args):
        ''' Accept an invite to an exchange
        '''
        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        if not db.verify_invitee(acct, memoid):
            msg.error_message("The Memo ID could not be verified.")
            return
        if int(db.check_status(memoid)) < 0:
            msg.error_message("The inviter has not yet authorized the exchange.")
            return            
        key = enter_key(acct)
        if db.accept_invite(acct, memoid, key):
            msg.message("The exchange invite has been accepted. To authorize this change send any amount " + 
                "of SBD to @steem-ax along with the following memo message. The SBD you send will be forwarded to the other party: \n\n    " + 
                memoid + ":accept")
        else:
            msg.error_message("Could not accept the invite.")


    def do_barter(self, args):
        ''' Barter on the percentage, ratio and duration of an exchange
        '''
        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        asin = db.verify_account(acct, memoid)
        if not asin:
            return
        if asin[0] == 1 and asin[1] == 0:
            acct1 = acct
            acct2 = asin[3]
        elif asin[0] == 0 and asin[1] == 1:
            acct1 = asin[2]
            acct2 = acct
        else:
            msg.error_message(acct + " is neither inviter or invitee. I know, it's weird.")
        print (acct1 + " is the inviter and " + acct2 + " is the invitee.")
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 1)
        dur = enter_duration()
        if not db.verify_memoid(acct, memoid):
            msg.message("Memo ID does not match the account provided.")
        else:
            msg.message("To initiate this barter send any amount SBD to @steem-ax with the following in the memo:\n\n    " +
                memoid + ":barter:" + per + ":" + ratio + ":" + dur)


    def do_cancel(self, args):
        ''' Cancel an invite to an exchange
        '''
        acct = enter_account_name(1, "")
        memoid = enter_memo_id(acct)
        if not db.verify_account(acct, memoid):
            return
        if db.cancel(acct, memoid):
            msg.message("The exchange has been canceled")
        else:
            msg.error_message("Could not cancel the exchange")


    def do_eligible(self, args):
        ''' Find out if a certain percentage and ratio between two accounts will create an eligible exchange
        '''
        acct1 = enter_account_name(1, "verbose")    
        acct2 = enter_account_name(0, "verbose")
        per = enter_percentage(acct1)
        ratio = enter_ratio(acct1, acct2, per, 0)


    def do_account(self, args):
        ''' Find and verify a Steemit account and see if it has started an exchange
        '''
        acct = enter_account_name(1, "verbose")
        db.verify_account(acct, "")


    def do_pool(self, args):
        ''' Display current Steemit Reward Balance, Recent Claims and price of STEEM
        '''
        xverify.get_steemit_balances()


    # Quit

    def do_quit(self, args):
        """Quits the program."""
        print ("Quitting.")
        raise SystemExit


# Run as main

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    run()

# EOF

