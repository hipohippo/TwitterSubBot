#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, splitCommand, matchKey, autoDestroy, tryDelete, commitRepo, removeOldFiles
from telegram.ext import MessageHandler, Filters
import threading
import twitter_2_album
import album_sender
from db import blocklist, existing, subscription
from common import tele, debug_group, twitterApi
from util import getHash, passFilter
import random

processed_channels = set()

def getStatuses(key):
	try:
		if key == 'hometimeline':
			return twitterApi.home_timeline()
		if isinstance(key, int):
			return twitterApi.user_timeline(key)
		return twitterApi.search(key, result_type='popular')
	except Exception as e:
		print('getStatuses fail', str(e), key)
		return []

def shouldProcess(channel, status, key):
	if channel.id in processed_channels:
		return False
	if status._json.get('in_reply_to_status_id'):
		return False
	if not passFilter(channel, status, key):
		return False
	if status.id < 1361617669598957569:
		return False # timestamp cut
	thash = str(getHash(status)) + str(channel.id)
	if not existing.add(thash):
		return False
	processed_channels.add(channel.id)
	return True

def shouldSendAlbum(channel, album):
	thash = str(''.join(album.cap[:20].split())) + str(channel.id)
	if not existing.add(thash):
		return False
	if album.video or album.imgs:
		return True
	return len(album.cap) > 20

@log_on_fail(debug_group)
def loopImp():
	removeOldFiles('tmp')
	global processed_channels 
	processed_channels = set()
	channels = list(subscription.getChannels())
	for key in subscription.keys():
		if key != 'hometimeline' and isinstance(key, str) and random.random() > 0.1:
			continue
		for status in getStatuses(key):
			# print(status.lang)
			# print(status.entities.get('media'))
			# print('http://twitter.com/%s/status/%s' % (
			# 	status.user.screen_name or status.user.id, status.id))
			for channel in channels:
				if shouldProcess(channel, status, key):
					try:
						album = twitter_2_album.get(str(status.id), 
							origin = [str(channel.id), channel.username])
						if shouldSendAlbum(channel, album):
							album_sender.send_v2(channel, album)
					except Exception as e:
						print('send fail', channel.id, str(e), status.id)	

def twitterLoop():
	loopImp()
	threading.Timer(10 * 60, twitterLoop).start()

def handleAdmin(msg, command, text):
	if not text:
		return
	success = False
	if command == '/abl':
		blocklist.add(text)
		success = True
	if success:
		autoDestroy(msg.reply_text('success'), 0.1)
		tryDelete(msg)
		commitRepo(delay_minute=0)

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.effective_message
	command, text = splitCommand(msg.text)
	if msg.chat.username in ['b4cxb', 'twitter_read']:
		handleAdmin(msg, command, text)
	if not msg or not msg.text.startswith('/tw'):
		return
	success = False
	if 'unsub' in command:
		subscription.remove(msg.chat_id, text)
		success = True
	elif 'sub' in command:
		subscription.add(msg.chat_id, text)
		success = True
	print('here')
	r = msg.reply_text(subscription.getSubscription(msg.chat_id), 
		parse_mode='markdown', disable_web_page_preview=True)
	if msg.chat_id < 0:
		tryDelete(msg)
		if success:
			autoDestroy(r, 0.1)

with open('help.md') as f:
	HELP_MESSAGE = f.read()

def handleHelp(update, context):
	update.message.reply_text(HELP_MESSAGE)

def handleStart(update, context):
	if 'start' in update.message.text:
		update.message.reply_text(HELP_MESSAGE)

if __name__ == '__main__':
	threading.Timer(1, twitterLoop).start() 
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(Filters.private & (~Filters.command), handleHelp))
	dp.add_handler(MessageHandler(Filters.private & Filters.command, handleStart), group=2)
	tele.start_polling()
	tele.idle()