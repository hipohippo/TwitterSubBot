#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, splitCommand, matchKey, autoDestroy, tryDelete, commitRepo
from telegram.ext import MessageHandler, Filters
import threading
import twitter_2_album
import album_sender
from .db import popularlist, blocklist, existing, subscription
from .common import tele, debug_group, twitterApi

def getRetweetedId(status):
	return status._json.get('retweeted_status', {}).get('id')

@log_on_fail(debug_group)
def loopImp():
	for key in list(subscription.keys()):
		for status in twitterApi.search(key, result_type='popular'):
			if 'id' not in status._json or not shouldProcess(status._json, db):
				continue
			if not db.existing.add(status.id):
				continue
			rid = getRetweetedId(status)
			if rid and not db.existing.add(rid):
				continue
			album = twitter_2_album.get(str(status.id))
			for chat_id in subscription.key_sub.copy():
				if (key not in subscription.key_sub[chat_id] and 
					not matchKey(album.cap, subscription.key_sub[chat_id])):
					continue
				try:	
					channel = tele.bot.get_chat(chat_id)	
					album_sender.send_v2(channel, album)
				except Exception as e:
					print('send fail for key', chat_id, str(e))	
					continue

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
	if command == '/apl':
		popularlist.add(text)
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
	r = msg.reply_text(subscription.getSubcription(msg.chat_id), 
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