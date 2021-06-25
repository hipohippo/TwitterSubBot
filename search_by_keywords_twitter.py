#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, matchKey
import twitter_2_album
import album_sender
from db import existing
from common import debug_group, twitterApi, bot
from util import getHash, passFilter
import plain_db

channel = bot.getChat(-1001401112463)
keywords = plain_db.loadKeyOnlyDB('keywords')
queue = [('hometimeline', 100)] # change to 1000

def getSearchResult(key, count):
	if key == 'hometimeline':
		return twitterApi.home_timeline(count=count)
	return twitterApi.user_timeline(key, count=count)

def shouldSendAlbum(channel, album):
	thash = str(''.join(album.cap[:20].split())) + str(channel.id)
	if not existing.add(thash):
		return False
	if album.video or album.imgs:
		return True
	return len(album.cap) > 20

def send(status):
	thash = str(getHash(status)) + str(channel.id)
	if not existing.add(thash):
		return
	album = twitter_2_album.get(str(status.id), 
		origin = [str(channel.id), channel.username])
	if shouldSendAlbum(channel, album):
		try:
			album_sender.send_v2(channel, album)
		except:
			debug_group.send_message('send fail. error: %s, url: %s' % (e, album.url))	

@log_on_fail(debug_group)
def search(key, count):
	for status in getSearchResult(key, count) or []:
		if status._json.get('in_reply_to_status_id'):
			continue
		if not passFilter(channel, status, key):
			continue
		if not matchKey(str(status), keywords.items()):
			continue
		send(status)
		print(status)

def runsearch():
	pivot = 0
	while len(queue) > pivot:
		key, count = queue[pivot]
		search(key, count)
		pivot += 1

# if __name__ == '__main__':
# 	search('hometimeline', 1000)

