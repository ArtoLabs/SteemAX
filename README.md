# SteemAX

SteemAX is a web application that allows a Steemian to barter with other Steemians for an automatic exchange of upvotes for an agreed duration.

SteemAX uses Python 3.5, MySQL and the [SimpleSteem](https://github.com/artolabs/simplesteem) library to utilize the [Steemit/Steem](https://github.com/steemit/steem) blockchain technology. SteemAX also uses [ScreenLogger](https://github.com/artolabs/screenlogger) to print to screen and log error messages 

SteemAX provides a way for Steemians (users of [Steemit.com](https://www.steemit.com)) to barter and make agreements on exchanging upvotes with each other for a set period of time. They do this through a barter system, each taking turns bidding on the amount of their upvotes they would like to exchange with each other. The upvotes are placed automatically by SteemAX for the agreed upon time period.

### Process

To start the process the inviter chooses a percentage of their upvote to exchange, as well as the ratio between upvotes and the number of days the auto-upvote exchange should take place. A unique Memo ID is generated which the inviter sends along with 0.001 SBD (or more) to SteemAX, which in turn forwards the amount to the invitee along with an invitation acceptance link. The invitee can choose to decline, accept or barter. If the invitee chooses barter they can adjust the percentage of the inviter's upvote, the ratio between upvotes, and the duration. If the invitee wishes to barter based on their own upvote value they can decline then start a new invitation. For authentication, all barter offers and invitations will be placed, first by entering the barter values into SteemAX, then authenticating by sending at least 0.001 SBD, along with the Memo ID, from the invitee/inviter's Steemit wallet to SteemAX. SteemAX will never keep the SBD sent but instead forwards it to the invitee/inviter. Once a Steemian accepts the offer, the auto-upvote exchanges take place with the following rules.

### Exchange Rules

SteemAX will periodically check the eligibility of the exchange participant's posts and if the following rules are met an exchange of upvotes will automatically take place.

1) Both accounts must have a recent post (not older than 5 days)

2) Only a new post since the last auto-upvote exchange is eligible. Upvotes are not retro-active.

3) If more than one post meets the criteria above, the most recent post will be used.

# Development

SteemAX is currently in the development phase with most of the core features already present in command line form. The current working version of SteemAX can be downloaded and installed using either git clone or pip. Functionality for creating an invite, bartering, canceling, determining post eligibility, as well as the process of determining vote exchange values based on the current state of the Steem blockchain, have already been created.

SteemAX can also be found online in beta/testing form at https://steemax.trade where further development on the web interface will take place.


### Instructions for installing SteemAX on Ubuntu 16.04

[Please see INSTALLATION.md](https://github.com/ArtoLabs/SteemAX/blob/master/INSTALLATION.md)

Please also reference the [installation instructions for SimpleSteem](https://github.com/ArtoLabs/SimpleSteem/blob/master/INSTALLATION.md)

# Instructions for use

Once SteemAX has been installed and the database has been set up (using the instructions below), simply type "steemax" at the Ubuntu command prompt. If this is the first time SteemAX has been run, the SteemAX database tables will be created and initialized, then you will be taken to the SteemAX command prompt. Type "help" to get a list of SteemAX commands.

#### `   ** Welcome to SteemAX **   `

You will see this greeting when first running SteemAX.

#### `[steemax]# adduser`

Starts the process to generate a refresh token using SteemConnect via the command line. In the first step the authorization URL is presented and then the user is prompted from the refresh token. The user can then cut and paste this into a browser in which they will be asked to authenticate and grant steemax.app the appropriate permissions. When SteemConnect redirects to the callback URL the refresh token can be cut and paste from the browser address bar back to the command line. Once entered, the refresh token is authenticated and the user's account name is retrieved via SteemConnect along with an access token. Both tokens and the account name are compared to the database and if no user with that name exists a new account is created. 


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

Typing in the command "barter" at the steemax command prompt allows an Inviter or Invitee to modify the parameters of the exchange. Regardless of who starts the barter process, the parameters always affect the Inviter's upvote. If the Invitee wishes to exchange based on the value of their upvote they can cancel the exchange and start a new one as the Inviter. Whoever starts the barter will be asked the following questions:

1) Account name, either inviter or invitee.

2) Memo ID that was generated during the invite process.

3) Percentage of inviter's upvote to be exchanged.

4) Ratio between the two account's upvote values. This is defaulted to 1 to 1.

5) Duration, in the number of days, for which the exchange should take place.

Once all information has been entered the one making the barter must send at least 0.001 SBD along with the Memo ID to SteemAX so that their account can be authenticated.


#### `[steemax]# cancel`

Typing in the command "cancel" at the steemax command prompt asks two questions in order to cancel the auto-upvote exchange.

1) Account name of the one accepting. This will normally be the invitee unless a barter process has been started.

2) Memo ID generated during the invite process.

Once all information has been entered the one cancelling must send at least 0.001 SBD along with the Memo ID to SteemAX so that their account can be authenticated.

#### `[steemax]# account`

Typing in the command "account" at the steemax command prompt allows the user to enter a Steemit.com account name to verify it's existence. If the account exists SteemAX will return the the accounts' Steem Power, current Voting Power, and current Upvote Value.

#### `[steemax]# eligible`

Typing in the command "eligible" at the steemax command prompt allows the user to enter the same information as if they were starting an invite but without actually creating an invite so that it can be worked out what percentage and ratio  might be best between the two accounts. Please see the 'invite' command for more information.

#### `[steemax]# pool`

Typing in the command "pool" at the steemax command prompt brings up the relevant information necessary for calculating the Steemit Reward Pool and the value of a Steemit account's upvote. SteemAX displays the current Reward Balance, the Recent Claims and the current price of Steem as delivered by the Witness Price Feed.

#### `[steemax]# run`

Runs the auto exchange eleigibilty algorithm for every completed and accepted transaction in the database then exchanges votes.


#### `[steemax]# process`

Fetches all the transaction history from @steem-ax and processes the action commands embedded in the memo messages based on Memo ID, then sends the appropriate reaction message to the appropriate account via forwarding (or refunding) the amount sent to commence the action.


