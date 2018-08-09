#!/usr/bin/python3

import re


def filter_token (string):
    string = re.sub(r'[^A-Za-z0-9\-\_\.]', 
                '', str(string))
    string = string[0:500]
    if string is None:
        string = "0"
    return string


def filter_account (string):
    string = re.sub(r'[^A-Za-z0-9\-\_\.]', 
                '', str(string))
    string = string[0:32]
    if string is None:
        string = " "
    return string


def filter_number (string, limit=100):
    string = re.sub(r'[^0-9\.]', 
                '', str(string))
    string = string[0:6]
    if float(string) < 0.001:
        string = "1"
    if float(string) > limit:
        string = limit
    return string
