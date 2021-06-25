#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, matchKey, commitRepo, removeOldFiles
import twitter_2_album
import album_sender
from db import blocklist, existing, subscription
from common import tele, debug_group, twitterApi, logger, bot
from util import getHash, passFilter, getCount
import random
import time

channel = bot.getChat(1001401112463)
keywords = plain_db.loadKeyOnlyDB('keywords')

def search(key, count):
	



# if __name__ == '__main__':
# 	search('hometimeline', 1000)

