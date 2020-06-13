#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import clearUrl, log_on_fail, removeOldFiles, commitRepo, splitCommand
from telegram.ext import Updater, MessageHandler, Filters
import yaml
import album_sender
from soup_get import SoupGet, Timer
from db import DB
import threading
import weibo_2_album
import urllib
from util import shouldSend

db = DB()

with open('credential') as f:
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


class TwitterListener(tweepy.StreamListener):
	def on_data(self, data):
		global record
		try:
			tweet_data = json.loads(data)
			if tweet_data.get('in_reply_to_status_id_str') or not tweet_data.get('user') or \
				tweet_data.get('quoted_status'):
				return
			tuid = tweet_data['user']['id_str']
			chat_ids = getSubscribers(tuid)
			if not chat_ids:
				return
			content = getContent(tweet_data)
			url_info = getUrlInfo(tweet_data)
			key_suffix = getKey(content, url_info)
			content = tweet_data['user']['name'] + ' | ' + formatContent(content, url_info)
			for chat_id in chat_ids:
				key = str(chat_id) + key_suffix
				r = updater.bot.send_message(chat_id=chat_id, text=content)
				if key in record:
					updater.bot.delete_message(chat_id=chat_id, message_id=record[key])
				record[key] = r['message_id']
		except Exception as e:
			print(e)
			tb.print_exc()

	def on_error(self, status_code):
		print('on_error = ' + str(status_code))
		tb.print_exc()

def twitterPush():
	global twitterStream
	global twitterApi
	print('loading/reloading twitter subscription')
	if twitterStream:
		twitterStream.disconnect()
	twitterListener = TwitterListener()
	twitterStream = tweepy.Stream(auth=twitterApi.auth, listener=twitterListener)
	twitterStream.filter(follow=db.getUsers())
	twitterStream.track(follow=db.getKeywords()) # need two stream

def twitterRestart():
	t = threading.Thread(target=twitterPush)
	t.start()

def updateSubInfo(msg, bot):
	try:
		saveSubscription()
		twitterRestart()
		info = 'Twitter Subscription List: \n' +  '\n'.join(sorted(SUBSCRIPTION[str(msg.chat_id)].values()))
		msg.reply_text(info, quote=False, parse_mode='Markdown', disable_web_page_preview=True)
	except Exception as e:
		print(e)
		tb.print_exc()

def getTwitterUser(link):
	global twitterApi
	screenname = [x for x in link.split('/') if x][-1]
	user = twitterApi.get_user(screenname)
	return str(user.id), '[' + user.name + '](twitter.com/' + str(user.screen_name) + ')'


auth = tweepy.OAuthHandler(CREDENTIALS['twitter_consumer_key'], CREDENTIALS['twitter_consumer_secret'])
auth.set_access_token(CREDENTIALS['twitter_access_token'], CREDENTIALS['twitter_access_secret'])
twitterApi = tweepy.API(auth)

def twitterLoop():
	try:
		if not twitterStream or not twitterStream.running:
			twitterRestart()
	except Exception as e:
		print(e)
		tb.print_exc()
	threading.Timer(10 * 60, twitterLoop).start()

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.effective_message
	if not msg or not msg.text.startswith('/tw'):
		return
	command, text = splitCommand(msg.text)
	if 'unsub' in command:
		db.subscription.remove(msg.chat_id, text)
	elif 'sub' in command:
		db.subscription.add(msg.chat_id, text)
	msg.reply_text(db.subscription.get(msg.chat_id))

def handleHelp(update, context):
	update.message.reply_text(HELP_MESSAGE)

def handleStart(update, context):
	if 'start' in update.message.text:
		update.message.reply_text(HELP_MESSAGE)

if __name__ == '__main__':
	threading.Thread(twitterLoop).start() 
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(Filters.private & (~Filters.command), handleHelp))
	dp.add_handler(MessageHandler(Filters.private & Filters.command, handleStart), group=2)
	tele.start_polling()
	tele.idle()