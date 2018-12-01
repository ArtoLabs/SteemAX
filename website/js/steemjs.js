var reward_fund = 0;
var recent_claims = 0;
var price_of_steem = 0;
var steem_per_mvests = 0;
var reserve_rate = 0;
var myvote = 0;
var theirvote = 0;
var myaccountname = "";
var exceeds = false;
var vote1 = 0;
var vote2 = 0;
var votecut = 0;
var account1 = "";
var account2 = "";
var formstate = 0;
var itemshowing = 0;
var currentbarterid = 0;
var invalidratio = 0;
var menuopen = false;
/* Functions using steem.js to fetch global properties and account vote values */
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
/* The following functions were copied directly from steem-python as steem.js
did not have similar functions and these values are needed for calculating vote values */
function steem_callback () {
    get_all_votes();
    disableform();
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
/* The get_vote_value function is at the heart of the script: it retrieves
a steemit account using steem.js then calculates the vote value based on
global properties fetched at page initialization */
function get_vote_value(accountname, weight, flag, id) {
    var regex = new RegExp('[^A-Za-z0-9\\.\\-\\_]', 'g');
    accountname = accountname.replace(regex, '');
    if (flag === 2) {
        document.getElementById("accountbox").value = accountname;
    }
    if (accountname === "steem-ax") {
        disableform();
        input_error(document.getElementById("accountbox"));
        document.getElementById("errormsg").innerHTML = "You may not create an exchange with @steem-ax.";
        return false;
    }
    if (accountname === myaccountname) {
        disableform();
        input_error(document.getElementById("accountbox"));
        document.getElementById("errormsg").innerHTML = "You may not exchange with yourself, Silly.";
        return false;
    }
    weight = weight * 100;
    steem.api.getAccounts([accountname], function(err, result) {
        if ((result != null) && (result != "")){
            var vesting_shares = parseFloat(result[0]['vesting_shares'].replace(" VESTS", ""));
            var delegated_vesting_shares = parseFloat(result[0]['delegated_vesting_shares'].replace(" VESTS", ""));
            var received_vesting_shares = parseFloat(result[0]['received_vesting_shares'].replace(" VESTS", ""));
            var totalvests = vesting_shares - delegated_vesting_shares + received_vesting_shares;
            var steem_power = vests_to_sp(totalvests);
            var rshares = sp_to_rshares(steem_power, 10000, weight);
            var vote_value = rshares_to_steem(rshares);

            // Flag 1 is raised when retreiving the vote value of the main account
            if (flag === 1) {
                myvote = vote_value;
                myaccountname = accountname;
                document.getElementById(accountname+"vote").innerHTML = '@' + accountname + ' $' + parseFloat(vote_value).toFixed(4);
            }
            /* Flag 2 is raised when retreiving the vote value for 
            the account entered into the form on the index page.*/
            if (flag === 2) {
                theirvote = vote_value;
                document.getElementById("errormsg").innerHTML = "@" + accountname +  " $" + parseFloat(vote_value).toFixed(4);
                enableform();
                input_correct(document.getElementById("accountbox"));
            }
            /* Flag 3 is raised when submitting the form on the index page and
            ensures the account name is still valid */
            if (flag === 3) {
                theirvote = vote_value;
                enableform();
                verifyform_callback();
            }
            /* Flag 4 is raised when retreiving the vote value of an account that is
            listed on the exchange table on the steemax.info page.   */
            if (flag === 4) {
                document.getElementById("votevalue"+id).value = vote_value;
                compare_votes_info_callback(id);
            }
            /* Flag 5 is raised when retrieving the vote value for the account being compared
            in the barter pop-up box on steemax.info  */
            if (flag === 5) {
                document.getElementById("votevalue"+id).value = vote_value;
                compare_votes_index(id);
            }
        }
        else if ((flag > 1) && (flag != 4)){
            disableform();
            input_error(document.getElementById("accountbox"));
            document.getElementById("errormsg").innerHTML = "Invalid account name.";
            if (flag === 3) {
                verifyform_callback();
            }
        }
    });
}
/* Functions for validating the the data entered into form on the index page */ 
function enableform () {
    //document.getElementById("percentage").focus();
    formstate = 1;
}
function disableform () {
    formstate = 0;
}
function input_error(obj) {
    obj.className = "inputshadowerror";
    if (document.getElementById("errormsg")) {
        document.getElementById("errormsg").style.color = "#ff9f51";
    }
} 
function input_correct(obj) {
    obj.className = "inputshadow";
    if (document.getElementById("errormsg")) {
        document.getElementById("errormsg").style.color = "#333333";
    }
}
function fix_values(per, ratio) {
    per = document.getElementById("percentage");
    ratio = document.getElementById("ratio");
    if (per.value > 100) {per.value = 100;}
    else if (per.value < 1) {per.value = 1;}
    if (ratio.value > 1000) {ratio.value = 1000;}
    else if (ratio.value < 0.001) {ratio.value = 1;}
}
function verifyform() {
    var regex = new RegExp('[^0-9\\.]', 'g');
    per = document.getElementById("percentage").value;
    per = per.replace(regex, '');
    document.getElementById("percentage").value = per;
    ratio = document.getElementById("ratio").value;
    ratio = ratio.replace(regex, '');
    document.getElementById("ratio").value = ratio;
    dur = document.getElementById("duration").value;
    dur = dur.replace(regex, '');
    document.getElementById("duration").value = dur;
    acctname = document.getElementById("accountbox").value;
    var regex = new RegExp('[^A-Za-z0-9\\.\\-\\_]', 'g');
    acctname = acctname.replace(regex, '');
    document.getElementById("accountbox").value = acctname;
    if (acctname === "steem-ax") {
        alert("You may not create an exchange with @steem-ax.");
        return false;
    }
    if (acctname === myaccountname) {
        alert("You may not exchange with yourself, Silly.");
        return false;
    }
    if (acctname === "") {
        alert("Please enter an Steemit.com account name.");
        return false;
    }
    else if ((per < 0) || (per > 100)) {
        input_error(document.getElementById("percentage"));
        alert("Please enter a percentage between 1 and 100.");
        fix_values();
        return false;
    }
    else if ((ratio < 0.001) || (ratio > 1000)) {
        input_error(document.getElementById("ratio"));
        alert("Please enter a ratio between 0.001 and 1000.");
        fix_values();
        return false;
    }
    else if (invalidratio === 1) {
        input_error(document.getElementById("ratio"));
        alert("Please enter a valid ratio.");
    }
    else if ((dur < 7) || (dur > 365)) {
        alert("Please enter a duration between 7 days and 365 days.");
        return false;
    }
    else {
        document.getElementById("exchange-button").style.display = "none";
        document.getElementById("loadergif").style.display = "block";
        //document.getElementById("accountbox").focus();
        get_vote_value(acctname, 100, 3, 0);
    }
}
function verifyform_callback() {
    if (formstate === 1) {
        //document.getElementById('axform').submit();
        addInvite();
    }
    else { 
        alert("Please enter a valid account name.");
        document.getElementById("exchange-button").style.display = "block";
        document.getElementById("loadergif").style.display = "none";
    }
}
/* Functions for calculating vote values */
function assign_votes(id) {
    regex = new RegExp('[^A-Za-z0-9\\.\\-\\_]', 'g');
    if (id > 0) {
        var otheraccount = document.getElementById("otheraccount"+id).value.replace(regex, '');
        var votevalue = document.getElementById("votevalue"+id).value;
        if (document.getElementById("invitee"+id).value == 0) {
            vote1 = myvote;
            vote2 = votevalue;
            account1 = myaccountname;
            account2 = otheraccount;
        }
        else {
            vote2 = myvote;
            vote1 = votevalue;
            account2 = myaccountname;
            account1 = otheraccount;
        }
    }
    else {
        vote1 = myvote;
        vote2 = theirvote;
        account1 = myaccountname;
        account2 = document.getElementById("accountbox").value.replace(regex, '');
    }
}
function calc_vote1(percentage) {
    vote1 = vote1 * (percentage / 100);
    vote1 = parseFloat(vote1).toFixed(4);
}
function calc_vote2(ratio) {
    votecut = ((vote1 / vote2) * 100) / ratio;
    if (votecut < 1) {exceeds = true;}
    if (votecut > 100) {exceeds = true;}
    vote2 = vote2 * (votecut / 100);
    vote2 = parseFloat(vote2).toFixed(4);
    if (vote2 <= 0.0001) { exceeds = true; }
}
function calc_votes(id) {

    var regex = new RegExp('[^0-9\\.]', 'g');
    var ratio = 0;
    var percentage = 0;
    if (id > 0) {
        percentage = document.getElementById("percentage"+id).value.replace(regex, '');
        ratio = document.getElementById("ratio"+id).value.replace(regex, '');
    }
    else {
        percentage = document.getElementById("percentage").value.replace(regex, '');
        ratio = document.getElementById("ratio").value.replace(regex, '');
    }
    if (percentage > 100) { percentage = 100; }
    if (percentage < 1) { percentage = 1; }
    if (ratio > 1000) { ratio = 1000; }
    if ((ratio < 0.001) && (ratio != 0)) { ratio = 0.001; }
    if (id > 0) {
        document.getElementById("percentage"+id).value = percentage;
        document.getElementById("ratio"+id).value = ratio;
    }
    else {
        document.getElementById("percentage").value = percentage;
        document.getElementById("ratio").value = ratio;
    }
    calc_vote1(percentage);
    calc_vote2(ratio);
}
function compare_votes_info_callback(id) {
    assign_votes(id);
    calc_votes(id);
    document.getElementById("compare"+id).innerHTML = ("("+account1+") <b>$"+vote1+"</b> vs. ("+account2+") <b>$"+vote2+"</b>");
    show_item(id);
}
function compare_votes_info(id) {
    if (document.getElementById("votevalue"+id).value > 0) {
        compare_votes_info_callback(id);
    }
    else {
        regex = new RegExp('[^A-Za-z0-9\\.\\-\\_]', 'g');
        var otheraccount = document.getElementById("otheraccount"+id).value.replace(regex, '');
        get_vote_value(otheraccount, 100, 4, id);
    }
}
function compare_votes_index() {
    if ((formstate === 0) && (currentbarterid < 1)) {
        return;
    }
    exceeds = false;
    assign_votes(currentbarterid);
    calc_votes();
    var votediff = 0;
    if (exceeds) {
        if ((votecut < 1) || (vote2 <= 0.0001)) {
            votediff = vote1 - vote2;
            votediff = parseFloat(votediff).toFixed(6);
            if (document.getElementById("errormsg")) {
                document.getElementById("errormsg").innerHTML = ("Invalid ratio. Please lower by $" + votediff);
            }
        }
        if (votecut > 100) {
            votediff = vote2 - vote1;
            votediff = parseFloat(votediff).toFixed(6);
            if (document.getElementById("errormsg")) {
                document.getElementById("errormsg").innerHTML = ("Invalid ratio. Please raise by $" + votediff);
            }
        }
        input_error(document.getElementById("ratio"));
        invalidratio = 1;
    }
    else {
        if (document.getElementById("showinviter")) {
            document.getElementById("showinviter").innerHTML = account1+'<br>'+vote1;
            document.getElementById("showinvitee").innerHTML = account2+'<br>'+vote2;
        }
        if (document.getElementById("errormsg")) {
            document.getElementById("errormsg").innerHTML = account1+" ("+vote1+") vs<br>"+account2+" ("+vote2+")";
        }
        input_correct(document.getElementById("ratio"));
        input_correct(document.getElementById("percentage"));
        invalidratio = 0;
    }
}
/* functions used for the barter window and for controlling
css GUI features on steemax.info  */
function command(id, account, command) {
    if (command === "accept") {
        obj = document.getElementById("sendBtn"+id);
        obj.innerHTML = "Accept using Steem Connect";
        obj.className = 'button-blue';
        document.getElementById("sendText"+id).innerHTML = '<a href="javascript" onClick="manualSend('+id+'); return false;">Accept manually</a>';
    }
    else if (command === "cancel") {
        obj = document.getElementById("sendBtn"+id);
        obj.innerHTML = "Cancel using Steem Connect";
        obj.className = 'button-red';
        document.getElementById("sendText"+id).innerHTML = '<a href="javascript" onClick="manualSend('+id+'); return false;">Cancel manually</a>';
    }
    else if (command === "start") {
        obj = document.getElementById("sendBtn"+id);
        obj.innerHTML = "Send invite using Steem Connect";
        obj.className = 'button-blue';
        document.getElementById("sendText"+id).innerHTML = '<a href="javascript" onClick="manualSend('+id+'); return false;">Send invite manually</a>';
    }
    var memoid = document.getElementById("storedmemoid"+id).value;
    var memomsg = memoid + ":" + command;
    document.getElementById("memoid"+id).value = memomsg;
    compare_votes_info(id);
}
function show_item(id) {
    hide_item();
    var memo = document.getElementById("memo"+id);
    memo.style.display = 'block';
    memo.offsetHeight;
    memo.style.opacity = '1';
    itemshowing = id;
}
function hide_item() {
    if (document.getElementById("memo"+itemshowing)) {
        document.getElementById("memo"+itemshowing).style.display = 'none';
        document.getElementById("memo"+itemshowing).style.opacity = '0';
    }
}
function barter_window(id) {
    currentbarterid = id;
    var modal = document.getElementById("myModal");
    modal.style.display = 'block';
    modal.offsetHeight;
    modal.style.opacity = '1';
    var modalcontent = document.getElementById("modal-content");
    modalcontent.style.display = 'block';
    modalcontent.offsetHeight;
    modalcontent.style.opacity = '1';
    document.getElementById("percentage").value = document.getElementById("percentage"+id).value;
    document.getElementById("ratio").value = document.getElementById("ratio"+id).value;
    document.getElementById("duration").value = document.getElementById("duration"+id).value;
    if (document.getElementById("votevalue"+id).value > 0) {
        compare_votes_index(id);
    }
    else {
        get_vote_value(document.getElementById("otheraccount"+id).value, 100, 5, id);
        compare_votes_info(id);
    }
}
function close_modal() {
    document.getElementById("myModal").style.display = "none";
    document.getElementById("myModal").style.opacity = '0';
}
function make_barter_memo() {
    var memoid = document.getElementById("storedmemoid"+currentbarterid).value;
    var percentage = document.getElementById("percentage").value;
    var ratio = document.getElementById("ratio").value;
    var duration = document.getElementById("duration").value;
    if ((percentage < 0) || (percentage > 100)) {
        alert("Please enter a percentage between 1 and 100.");
        fix_values();
        return false;
    }
    else if ((ratio < 0.001) || (ratio > 1000)) {
        alert("Please enter a ratio between 0.001 and 1000.");
        fix_values();
        return false;
    }
    else if (invalidratio === 1) {
        input_error(document.getElementById("ratio"));
        alert("Please enter a valid ratio.");
        return false;
    }
    else if ((duration < 7) || (duration > 365)) {
        alert("Please enter a duration between 7 days and 365 days.");
        return false;
    }
    
    obj = document.getElementById("sendBtn"+currentbarterid);
    obj.innerHTML = "Send barter offer using Steem Connect";
    obj.className = 'button';
    var memomsg = memoid + ":barter" + ":" + percentage + ":" + ratio + ":" + duration;
    document.getElementById("memoid"+currentbarterid).value = memomsg;
    document.getElementById("sendText"+currentbarterid).innerHTML = '<a href="javascript" onClick="manualSend('+currentbarterid+'); return false;">Send barter offer manually</a>';
    close_modal();
    show_item(currentbarterid);
}
function onRangeChange(rangeInputElmt, listener, id) {
    // We create an event listener for both input and change in order
    // to be cross browser and mobile friendly.
    // inputEvtHasNeverFired ensures only one of the two is used.
    var inputEvtHasNeverFired = true;
    var rangeValue = {current: undefined, mostRecent: undefined};
    rangeInputElmt.addEventListener("input", function(evt) {
        inputEvtHasNeverFired = false;
        rangeValue.current = evt.target.value;
        if (rangeValue.current !== rangeValue.mostRecent) {listener(evt);}
        rangeValue.mostRecent = rangeValue.current;
    });
    rangeInputElmt.addEventListener("change", function(evt) {
        if (inputEvtHasNeverFired) {listener(evt);}
    }); 
}
var myListener = function(myEvt) {
    // The listener callback function adjusts the sliders value then
    // inserts it into the ratio box for further calculating.
    var ratio = 1;
    if (myEvt.target.value >= 210) { ratio = myEvt.target.value - 200; }
    else if (myEvt.target.value == 209) { ratio = 9.9; }
    else if ((myEvt.target.value < 209) && (myEvt.target.value > 120)) { 
        ratio = parseFloat((myEvt.target.value - 110) * 0.1).toFixed(1); 
    }
    else if (myEvt.target.value == 120) { ratio = 1; }
    else if ((myEvt.target.value <= 119) && (myEvt.target.value > 21)) { 
        ratio = (myEvt.target.value - 20) / 100; 
    }
    else {
        ratio = 0.01;
    }
    document.getElementById("ratio").value = ratio;
    compare_votes_index(currentbarterid);
};
function sendSbdToSteemax(account, id) {
    regex = new RegExp('[^A-Za-z0-9\\:\\.]', 'g');
    var memoid = document.getElementById("memoid"+id).value.replace(regex, '');
    var url = "https://steemconnect.com/sign/transfer?from="+account+"&to=steem-ax&amount=0.001%20SBD&memo="+memoid+"&redirect_uri=https://steemax.info/@"+account;
    window.location = (url);
}
function sendAll(command) {
    regex = new RegExp('[^A-Za-z0-9\\:\\.]', 'g');
    var ids;
    if (command === "accept") {
        ids = document.getElementById("allacceptids").value.split(",");
    }
    else if (command === "start") {
        ids = document.getElementById("allsendids").value.split(",");
    }
    else if (command === "cancel") {
        ids = document.getElementById("allcancelids").value.split(",");
    } 
    var memoid = document.getElementById("memoid"+ids[0]).value.replace(regex, '');
    memo = memoid+":"+command;
    for(i=1;i<ids.length;i++) {
        memoid = document.getElementById("memoid"+ids[i]).value.replace(regex, '');
        memo += "_"+memoid+":"+command;
    }
    sendamount = ids.length / 1000;
    var url = "https://steemconnect.com/sign/transfer?from="+myaccountname+"&to=steem-ax&amount="+sendamount+"%20SBD&memo="+memo+"&redirect_uri=https://steemax.info/@"+myaccountname;
    window.location = (url);
}
function showAllButtons() {
    var acceptids = document.getElementById("allacceptids").value.split(",");
    var sendids = document.getElementById("allsendids").value.split(",");
    var cancelids = document.getElementById("allcancelids").value.split(",");
    if (sendids.length > 1) {
        document.getElementById("sendall-button").style.display = 'block';
    }
    if (acceptids.length > 1) {
        document.getElementById("acceptall-button").style.display = 'block';
    }
    if (cancelids.length > 1) {
        document.getElementById("cancelall-button").style.display = 'block';
    }
}

/*  AJAX code used for submitting the invite creation form and incrementing
 the notice counter
*/
var httpObject;
function addInvite() {
    var regex = new RegExp('[^0-9\\.]', 'g');
    var per = document.getElementById("percentage").value.replace(regex, '');
    var ratio = document.getElementById("ratio").value.replace(regex, '');
    var dur = document.getElementById("duration").value.replace(regex, '');
    var regex = new RegExp('[^A-Za-z0-9\\.\\-\\_]', 'g');
    var acctname = document.getElementById("accountbox").value.replace(regex, '');
    var code = document.getElementById("code").value.replace(regex, '');
    var captcha = document.getElementById("g-recaptcha-response").value.replace(regex, '');
	var url = "https://www.steemax.trade/post.py?code=" + code + "&account=" + acctname + "&percentage=" + per + "&ratio=" + ratio + "&duration=" + dur + "&g-recaptcha-response=" + captcha + "&ajax=1";
    url = encodeURI(url);
	httpObject = loadAddInviteAJAX();
	getDynamicData(url);
}
function loadAddInviteAJAX() {
	var xhr_object = null;
	if(window.XMLHttpRequest) {xhr_object = new XMLHttpRequest();} 
	else if(window.ActiveXObject) {xhr_object = new ActiveXObject("Microsoft.XMLHTTP");} 
	else {alert("Your browser doesn't provide XMLHttprequest functionality"); return;}
	return xhr_object;
}
function getDynamicData(url) {
	httpObject.open('GET', url, true);
	httpObject.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	httpObject.onreadystatechange = callbackAddInviteFunction;
	httpObject.send(null);
}
function callbackAddInviteFunction() {
	if (httpObject.readyState != 4) {return 0;}
	else {
		var response = httpObject.responseText;
        var regex = new RegExp('[^0-9]', 'g');
		if (httpObject.status==200) {
            if (response.replace(regex, '') === "1") {
                addNotice();
            }
            else {
                alert(response);
                stopLoaderGif();
            }
        }
		else {
            alert(response);
            stopLoaderGif();
        }
	}
}
/* Code for displaying the pending invite count and notification bubble */
function showInviteCount() {
    ele = document.querySelector('.notice-bubble');
    var num = parseInt(ele.innerHTML);
    if (num > 0) { 
        ele.style.display = "block";
    }
    ele.classList.add('animating');
    removeAnimation();
}
function addNotice() {
    resetForm();
    stopLoaderGif();
    ele = document.querySelector('.notice-bubble');
    var num = parseInt(ele.innerHTML);
    if (num === 0) { 
        ele.style.display = "block";
    }
    ele.innerHTML = num + 1;
    ele.classList.add('animating');
    removeAnimation();
}
function removeAnimation(){
    setTimeout(function() {
        ele = document.querySelector('.notice-bubble');
        ele.classList.remove('animating');
    }, 1000);           
}
function resetForm() {
    document.getElementById("errormsg").style.color = "#ffffff";
    document.getElementById("errormsg").innerHTML = "Make another exchange invite";
    document.getElementById("percentage").value = "";
    document.getElementById("ratio").value = "1";
    document.getElementById("accountbox").value = "";
    theirvote = 0;
    exceeds = false;
    vote1 = 0;
    vote2 = 0;
    votecut = 0;
    account1 = "";
    account2 = "";
    formstate = 0;
}
function stopLoaderGif() {
    grecaptcha.reset();
    document.getElementById("loadergif").style.display = "none";
    document.getElementById("exchange-button").style.display = "inline-block";
    //document.getElementById("accountbox").focus();
}
function manualSend(id) {
    var memoid = document.getElementById("memoid"+id).value;
    document.getElementById("sendText"+id).innerHTML = "Send $0.001 SBD to @steem-ax with this in the memo:<br><input type='text' value='"+memoid+"'>";
    return false;
}
function openMenu () {
	if (menuopen) {
		document.getElementById("navmenu").style.left = "230px";
		document.getElementById("navmenu").style.opacity = "0";
		document.getElementById("hamburger-icon").style.transform = "rotate(0deg)"; 
		menuopen = false;
	}
	else {
		document.getElementById("navmenu").style.left = "0px";
		document.getElementById("navmenu").style.opacity = "1";
		document.getElementById("hamburger-icon").style.transform = "rotate(90deg)";
		menuopen = true;
	}
    return false;
}

