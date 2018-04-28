# SteemAX

A Steem blockchain auto-upvote exchange system.

SteemAX uses Python 3.0, MySQL and the [Steem-Python](https://github.com/steemit/steem-python) library to utilize the [Steemit/Steem](https://github.com/steemit/steem) blockchain technology.

# Concept

SteemAX provides a way for Steemians (users of [Steemit.com](https://www.steemit.com)) to barter and make agreements on exchanging upvotes with each other for a set period of time. They do this through a barter system, each taking turns bidding on the amount of thier upvotes they would like to exchange with each other. The upvotes are placed automatically by SteemAX for the agreed upon time period.

### Process

To start the process the inviter chooses a percentage of their upvote to exchange, as well as the ratio between upvotes and the number of days the auto-upvote exchange should take place. A unique Memo ID is generated which the inviter sends along with 0.001 SBD (or more) to SteemAX, which in turn forwards the amount to the invitee along with an invitation acceptance link. The invitee can choose to decline, accept or barter. If the invitee chooses barter they can adjust the percentage of the inviter's upvote, the ratio between upvotes, and the duration. If the invitee wishes to barter based on their own upvote value they can decline then start a new invitation. For authentication, all barter offers and invitations will be placed, first by entering the barter values into SteemAX, then authenticating by sending at least 0.001 SBD, along with the Memo ID, from the invitee/inviter's Steemit wallet to SteemAX. SteemAX will never keep the SBD sent but instead forwards it to the invitee/inviter. Once a Steemian accepts the offer, the auto-upvote exchanges take place with the following rules.

### Exchange Rules

SteemAX will periodicaly check the eligibility of the exchange participant's posts and if the following rules are met an exchange of upvotes will automatically take place.

1) Both accounts must have a recent post (not older than 5 days)

2) Only a new post since the last auto-upvote exchange is eligible. Upvotes are not retro-active.

3) If more than one post meets the criteria above, the most recent post will be used.

# Reality

SteemAX is currently in the development phase with most of the core features already present in command line form. Functionality for creating an invite, bartering, canceling, determining post eligibility, as well as the process of dertmining vote exchange values based on the current state of the Steem blockchain, have already been created. What's left is to create the Memo ID authentication process, and the shiny front-end, which most likely will be written with help from the [steem-js](https://github.com/steemit/steem-js) library. In it's current form, SteemAX is "disarmed" and does not actually exchange upvotes when it's run, but instead prints the message "Auto upvote exchange occured" when all eligibility requirements are met. SteemAX will be "armed" with the code necessary to exchange upvotes when most the bugs have been fixed and a stable version is running without problems.

# Instructions for use

Once SteemAX has been installed and the databse has been set up (using the instructions below), simply type "steemax" at the Ubuntu command prompt. If this is the first time SteemAX has been run, the SteemAX database tables will be created and initialized, then you will be taken to the SteemAX command prompt. Type "help" to get a list of SteemAX commands.

#### `   ** Welcome to SteemAX **   `

You will see this greeting when first running SteemAX.

#### `[steemax]# invite`

Typing the command "invite" at the steemax command prompt starts the invitation process. The inviter is asked the following questions:

1) Inviter's account name. This is the inviter's Steemit.com account name, entered without the @ symbol.

2) Invitee's account name. this is the invitee's Steemit.com account name.

3) Private Posting Key, which is found in the inviter's Steemit wallet. This is used to automate the upvote exchanges.

4) Percentage of the inviter's upvote the wish to exchange.

5) Ratio between the two account's upvote values. This is defaulted to 1 to 1.

6) Duration, in the number of days, for which the exchange should take place.

When all information is entered a unique Memo ID is generated that is then used to reference this exchange in all future transactions. When all functionality is present, the Inviter will be asked to send at least 0.001 SBD along with this Memo ID to SteemAX so that the Inviter's account can be authenticated.

#### `[steemax]# barter` 

Typing in the command "barter" at the steemax commnand prompt allows an Inviter or Invitee to modify the parameters of the exchange. Regardless of who starts the barter process, the parameters always affect the Inviter's upvote. If the Invitee wishes to exchange based on the value of their upvote they can cancel the exchange and start a new one as the Inviter. Whoever starts the barter will be asked the following questions:

1) Account name, either inviter or invitee.

2) Memo ID that was generated during the invite process.

3) Percentage of inviter's uvote to be exchanged.

4) Ratio between the two account's upvote values. This is defaulted to 1 to 1.

5) Duration, in the number of days, for which the exchange should take place.

Once all information has been entered the one making the barter must send at least 0.001 SBD along with the Memo ID to SteemAX so that thier account can be authenticated.

#### `[steemax]# accept`

Typing in the command "accept" at the steemax commnand prompt asks two questions then starts the auto-upvote exchange as was agreed upon.

1) Account name of the one accepting. This will normally be the invitee unless a barter process has been started.

2) Memo ID generated during the invite process.

#### `[steemax]# account`

Typing in the command "account" at the steemax command prompt allows the user to enter a Steemit.com account name to verify it's existence. If the account exists SteemAX will return the the accounts' Steem Power, current Voting Power, and current Upvote Value.

#### `[steemax]# eligible`

Typing in the command "eligible" at the steemax command prompt allows the user to enter the same information as if they were starting an invite but without actually creating an invite so that it can be worked out what percentage and ratio  might be best between the two accounts. Please see the 'invite' command for more information.

#### `[steemax]# pool`

Typing in the command "pool" at the steemax command prompt brings up the relevant information necessary for calculating the Steemit Reward Pool and the value of a Steemit account's upvote. SteemAX displays the current Reward Balance, the Recent Claims and the current price of Steem as delivered by the Witness Price Feed.

### Instructions for installing SteemAX on Ubuntu 16.04

[Please see INSTALLATION.md](https://github.com/ArtoLabs/SteemAX/blob/master/INSTALLATION.md)
