#!/usr/bin/python3

import logging

LOGFORMAT = "%(asctime)s %(levelname)s - %(message)s - %(pathname)s"
logging.basicConfig(filename = "error.log", level = logging.ERROR, format = LOGFORMAT)
logger = logging.getLogger()

class AXmsg:

    def __init__(self):
        self.mode = ""

    def x_message(self, msg):
        if self.mode != "quiet":
            print (msg)
        logger.info(msg)

    def x_error_message(self, msg):
        if self.mode != "quiet":
            print (msg)
        logger.error(msg)


# Run as main

if __name__ == "__main__":

    a = AXmsg()
    a.x_message("AXmsg class is up and running.")


# EOF
