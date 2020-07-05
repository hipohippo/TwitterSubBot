#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import tweepy

with open('CREDENTIALS') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
twitterApi = tweepy.API(auth)

# for status in twitterApi.user_timeline(id="bestsapphics"):
# 	print(status.id)

for status in twitterApi.search('女权'):
	print(status.id)