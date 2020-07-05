#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import tweepy
import twitter_2_album
import album_sender
from telegram.ext import Updater

with open('CREDENTIALS') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['bot'], use_context=True)  # @twitter_send_bot
debug_group = tele.bot.get_chat(420074357)

auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
twitterApi = tweepy.API(auth)

# for status in twitterApi.user_timeline(id="bestsapphics"):
# 	print(status.id)

for status in twitterApi.search('女权'):
	r = twitter_2_album.get(str(status.id))
	album_sender.send_v2(debug_group, r)