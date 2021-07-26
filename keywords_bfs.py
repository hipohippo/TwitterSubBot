#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, matchKey, getMatchedKey
import twitter_2_album
import album_sender
from db import existing, blocklist
from common import debug_group, twitterApi, bot
from util import getHash, getCount
import plain_db

channel = bot.getChat(-1001401112463)
keywords = plain_db.loadKeyOnlyDB('keywords')
queue = [('hometimeline', 200)]
existed_keys = set([None])

def getSearchResult(key, count):
	if key == 'hometimeline':
		return twitterApi.home_timeline(count=count)
	return twitterApi.user_timeline(user_id=key, count=count)

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
		except Exception as e:
			debug_group.send_message('send fail. error: %s, url: %s' % (e, album.url))	

def addKey(user, count, referer):
	if user.id not in existed_keys:
		existed_keys.add(user.id)
		queue.append((user.id, count))

@log_on_fail(debug_group)
def search(key, count):
	if count < 20:
		return
	for status in getSearchResult(key, count) or []:
		if status._json.get('in_reply_to_status_id'):
			continue
		if status.lang != 'zh' or getCount(status._json) < 200:
			continue
		if matchKey(str(status), blocklist.items()):
			continue
		if key == 'hometimeline':
			addKey(status.user, count, status.user)
		if not matchKey(status.text, keywords.items()):
			continue
		send(status)
		try:
			addKey(status.retweeted_status.user, count * 0.8, status.user)
		except:
			...

def runsearch():
	pivot = 0
	while len(queue) > pivot:
		key, count = queue[pivot]
		search(key, count)
		pivot += 1
	print('finish run search')

# if __name__ == '__main__':
# 	search('hometimeline', 1000)

