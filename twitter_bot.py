#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, splitCommand, matchKey
from telegram.ext import Updater, MessageHandler, Filters
import yaml
from db import DB
import threading
from stream import Stream, shouldProcess
import tweepy
import twitter_2_album
import album_sender

db = DB()

with open('CREDENTIALS') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot'], use_context=True)  # @twitter_send_bot
debug_group = tele.bot.get_chat(420074357)

HELP_MESSAGE = '''
Subscribe Twitter posts.

commands:
/tw_subscribe user_link/user_id/keywords
/tw_unsubscribe user_link/user_id/keywords
/tw_view - view current subscription

Can be used in group/channel also.

Github： https://github.com/gaoyunzhi/twitter_bot
'''

auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
twitterApi = tweepy.API(auth)

twitter_stream = Stream(db, twitterApi, tele.bot)

def getRetweetedId(status):
	return status._json.get('retweeted_status', {}).get('id')

@log_on_fail(debug_group)
def searchKeys():
	for key in list(db.sub.keys()):
		for status in twitterApi.search(key):
			if 'id' not status._json or not shouldProcess(status._json, db):
				continue
			if not self.db.existing.add(status.id):
				continue
			rid = getRetweetedId(status)
			if rid and not self.db.existing.add(rid):
				continue
			album = twitter_2_album.get(str(status.id))
			for chat_id in self.db.sub.key_sub.copy():
				if (key not in self.db.sub.key_sub[chat_id] and 
					not matchKey(r.cap, self.db.sub.key_sub[chat_id])):
					continue
				try:	
					channel = self.bot.get_chat(chat_id)	
					album_sender.send_v2(channel, album)
				except Exception as e:
					print(chat_id, str(e))	
					continue

def twitterLoop():
	try:
		twitter_stream.reload()
		db.reload()
	except Exception as e:
		debug_group.send_message('twitter_stream reload error ' + str(e))
	searchKeys()
	print('twitterLoop')
	threading.Timer(10 * 60, twitterLoop).start()

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.effective_message
	if not msg or not msg.text.startswith('/tw'):
		return
	command, text = splitCommand(msg.text)
	if 'unsub' in command:
		db.sub.remove(msg.chat_id, text, twitterApi)
		twitter_stream.forceReload()
	elif 'sub' in command:
		db.sub.add(msg.chat_id, text, twitterApi)
		twitter_stream.forceReload()
	msg.reply_text(db.sub.get(msg.chat_id, twitterApi), 
		parse_mode='markdown', disable_web_page_preview=True)

def handleHelp(update, context):
	update.message.reply_text(HELP_MESSAGE)

def handleStart(update, context):
	if 'start' in update.message.text:
		update.message.reply_text(HELP_MESSAGE)

if __name__ == '__main__':
	searchKeys()
	twitter_stream.forceReload()
	threading.Timer(10 * 60, twitterLoop).start() 
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(Filters.private & (~Filters.command), handleHelp))
	dp.add_handler(MessageHandler(Filters.private & Filters.command, handleStart), group=2)
	tele.start_polling()
# 	tele.idle()