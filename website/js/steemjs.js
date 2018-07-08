var reward_fund = 0;
var recent_claims = 0;
var price_of_steem = 0;
var steem_per_mvests = 0;
var reserve_rate = 0;
var myvote = 0;
var myaccountname = "";
var vote1 = 0;
var vote2 = 0;
var formstate = 0;
steem.api.getRewardFund("post", function(err, fund) {
    reward_fund = parseFloat(fund.reward_balance.replace(" STEEM", ""));
    recent_claims = parseInt(fund.recent_claims, 10);
    steem.api.getCurrentMedianHistoryPrice(function(err, price) {
        price_of_steem = parseFloat(price.base.replace(" SBD", ""));
        steem.api.getDynamicGlobalProperties(function(err, gprops) {
            var vfs = parseFloat(gprops.total_vesting_fund_steem.replace(" STEEM", ""));
            var tvs = parseFloat(gprops.total_vesting_shares.replace(" STEEM", ""));
            reserve_rate = parseFloat(gprops.vote_power_reserve_rate);
            steem_per_mvests = vfs / (tvs / 1000000);
            steem_callback();
        });
    });
});
function verifyform () {
    acctname = document.getElementById("account").value;
    get_vote_value(acctname, 100, 3);
}
function verifyform_callback() {
    if (formstate == 1) {
        document.getElementById('axform').submit();
    }
    else {
        alert("Please enter a valid account name.");
    }
}


function steem_callback () {
    get_all_votes();
    document.getElementById("percentage").setAttribute("disabled", true);
    document.getElementById("ratio").setAttribute("disabled", true);
    document.getElementById("duration").setAttribute("disabled", true);
    document.getElementById("button").setAttribute("disabled", true);
}
function vests_to_sp(vests) {
    return vests / 1000000 * steem_per_mvests;
}
function sp_to_vests(sp) {
    return sp * 1000000 / steem_per_mvests;
}
function sp_to_rshares(steempower, votepower, voteweight) {
    var vesting_shares = parseInt(sp_to_vests(steempower) * 1000000);
    var used_power = parseInt((votepower * voteweight) / 10000);
    var max_vote_denom = reserve_rate * (5 * 60 * 60 * 24) / (60 * 60 * 24);
    used_power = parseInt((used_power + max_vote_denom - 1) / max_vote_denom);
    var rshares = ((vesting_shares * used_power) / 10000);
    return rshares;
}
function rshares_to_steem(rshares) {
    return rshares * reward_fund / recent_claims * price_of_steem;
}



function enableform () {
    document.getElementById('accountbox').style.borderColor = "green";
    document.getElementById("percentage").disabled = false;
    document.getElementById("ratio").disabled = false;
    document.getElementById("duration").disabled = false;
    document.getElementById("button").disabled = false;
    formstate = 1;
}

function disableform () {
    document.getElementById('accountbox').style.borderColor = "red";
    document.getElementById("percentage").disabled = true;
    document.getElementById("ratio").disabled = true;
    document.getElementById("duration").disabled = true;
    document.getElementById("button").disabled = true;
    formstate = 0;
}

function get_vote_value(accountname, weight, flag) {

    weight = weight * 100;
    steem.api.getAccounts([accountname], function(err, result) {
        console.log(err, result)
        if (result[0] != null) {
            var vesting_shares = parseFloat(result[0]['vesting_shares'].replace(" VESTS", ""));
            var delegated_vesting_shares = parseFloat(result[0]['delegated_vesting_shares'].replace(" VESTS", ""));
            var received_vesting_shares = parseFloat(result[0]['received_vesting_shares'].replace(" VESTS", ""));
            var totalvests = vesting_shares - delegated_vesting_shares + received_vesting_shares;
            var steem_power = vests_to_sp(totalvests);
            var rshares = sp_to_rshares(steem_power, 10000, weight);
            var vote_value = rshares_to_steem(rshares);
            vote_value = parseFloat(vote_value).toFixed(4);
            if (flag == 1) {
                myvote = vote_value;
                myaccountname = accountname;
            }
            if (flag == 2) {
                vote2 = vote_value;
                enableform();
            }
            if (flag == 3) {
                vote2 = vote_value;
                enableform();
                verifyform_callback();
            }
            id = accountname + "vote";
            id2 = accountname + "votevalue";
            document.getElementById(id).innerHTML = 'Vote: $' + vote_value + ' STU';
            document.getElementById(id2).value = vote_value;
        }
        else if (flag > 1) {
            disableform();
            if (flag == 3) {
                verifyform_callback();
            }
        }
    });

}



function compare_votes(account) {
    var percentage = document.getElementById("percentage").value;
    var ratio = document.getElementById("ratio").value;
    var votevalue;
    var account1;
    var account2;
    if (document.getElementById(account + "votevalue")) {

        votevalue = document.getElementById(account + "votevalue").value;

        if (document.getElementById(account + "invitee").value == 1) {
            vote1 = myvote * (percentage / 100);
            vote2 = votevalue;
            account1 = myaccountname;
            account2 = account;
        }
        else {
            vote2 = myvote * (percentage / 100);
            vote1 = votevalue;
            account2 = myaccountname;
            account1 = account;
        }

    }
    else {
        vote1 = myvote * (percentage / 100);
        account1 = myaccountname;
        account2 = document.getElementById("account").value;
    }

    var votecut = ((vote1 / vote2) * 100) / ratio;

    var exceeds = 0;
    if (votecut < 1) {votecut = 1;exceeds = 1;}
    if (votecut > 100) {votecut = 100;exceeds = 1;}

    newvotevalue = vote2 * (votecut / 100);
   
    if (exceeds == 1) {
        if (votecut == 1) {
            votediff = newvotevalue - vote1;
            document.getElementById("errormsg").innerHTML = (account2 + "'s vote of " + newvotevalue 
                            + " will be larger than " + account1 
                            + "'s vote by: " + votediff);
        }
        if (votecut == 100) {
            votediff = vote1 - newvotevalue;
            document.getElementById("errormsg").innerHTML = (account1 + "'s vote of " + vote1 
                            + " will be larger than " + account2 
                            + "'s vote by: " + votediff);
        }
    }
    else {
        document.getElementById("errormsg").innerHTML = (account1 + " will upvote $" + vote1 
                + " and " + account2 + " will upvote $" + newvotevalue);
    }

}
