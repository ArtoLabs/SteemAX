SteemAX

A Steem blockchain auto-upvote exchange system.

SteemAX uses Python 3.0, MySQL and the Steem-Python library to utilize the Steemit/Steem blockchain technology.

Concept

SteemAX provides a way for Steemians (users of Steemit.com) to barter and make agreements on exchanging upvotes with each other for a set period of time. They do this through a barter system, each taking turns bidding on the amount of thier upvotes they would like to exchange with each other. The upvotes are placed automatically by SteemAX for the agreed upon time period.

Process

To start the process the inviter chooses a percentage of their upvote to exchange, as well as the ratio between upvotes and the number of days the auto-upvote exchange should take place. A unique Memo ID is generated which the inviter sends along with 0.001 SBD (or more) to SteemAX, which in turn forwards the amount to the invitee along with an invitation acceptance link. The invitee can choose to decline, accept or barter. If the invitee chooses barter they can adjust the percentage of the inviter's upvote, the ratio between upvotes, and the duration. If the invitee wishes to barter based on their own upvote value they can decline then start a new invitation. For authentication, all barter offers and invitations will be placed, first by entering the barter values into SteemAX, then authenticating by sending at least 0.001 SBD, along with the Memo ID, from the invitee/inviter's Steemit wallet to SteemAX. SteemAX will never keep the SBD sent but instead forwards it to the invitee/inviter. Once a Steemian accepts the offer, the auto-upvote exchanges take place with the following rules.

Exchange Rules

SteemAX will periodicaly check the eligibility of the exchange participant's posts and if the following rules are met an exchange of upvotes will automatically take place.

1) Both accounts must have a recent post (not older than 5 days)

2) Only a new post since the last auto-upvote exchange is eligible. Upvotes are not retro-active.

3) If more than one post meets the criteria above, the most recent post will be used.

Reality

SteemAX is currently in the development phase with most of the core features already present in command line form. Functionality for creating an invite, bartering, canceling, determining post eligibility, as well as the process of dertmining vote exchange values based on the current state of the Steem blockchain, have already been created. What's left is to create the Memo ID authentication process, and the shiny front-end, which most likely will be written with help from the steem-js library. In it's current form, SteemAX is "disarmed" and does not actually exchange upvotes when it's run, but instead prints the message "Auto upvote exchange occured" when all eligibility requirements are met.

Instructions for use

Once SteemAX has been installed and the databse has been set up (using the instructions below), simply type "steemax" at the Ubuntu command prompt. If this is the first time SteemAX has been run, the SteemAX database tables will be created and initialized, then you will be taken to the SteemAX command prompt. Type "help" to get a list of SteemAX commands.


Instructions for installing SteemAX on Ubuntu 16.04

Be sure to write down the root password that you will create when installing MySQL as you will need it in the following steps. Instructions for setting up the SteemAX database and MySQL user are at the end.

INSTALL WITH PIP

sudo apt install python3 python3-pip libssl-dev python3-dev mysql-server

pip3 install steemax --user pip

INSTALL WITH GIT

sudo apt install python3 python3-pip libssl-dev python3-dev mysql-server

pip3 install steem --user pip

git clone https://github.com/ArtoLabs/SteemAX.git

OPTIONAL

cd ~/SteemAX

pip3 install . --user pip

OR RUN AS

python3 steemax.py

SETUP AFTER INSTALL

mysql_secure_installation

mysql -u root -p

CREATE DATABASE steemax;

CREATE USER 'steemax'@'localhost' IDENTIFIED BY 'SteemAX_pass23';

GRANT ALL PRIVILEGES ON steemax.* to 'steemax'@'localhost';

exit



