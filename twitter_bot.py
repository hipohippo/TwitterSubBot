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

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot'], use_context=True)  # @weibo_subscription_bot
debug_group = tele.bot.get_chat(420074357)

HELP_MESSAGE = '''
本bot负责订阅微博信息。

可用命令：
/wb_subscribe 用户ID/关键词/用户链接 - 订阅
/wb_unsubscribe 用户ID/关键词/用户链接 - 取消订阅
/wb_view - 查看当前订阅

本bot在群组/频道中亦可使用。

Github： https://github.com/gaoyunzhi/weibo_subscription_bot
'''

sg = SoupGet()
db = DB()
	
def getResults(url):
	content = sg.getContent(url)
	content = yaml.load(content, Loader=yaml.FullLoader)
	for card in content['data']['cards']:
		if 'scheme' not in card:
			continue
		if 'type=uid' not in url and not shouldSend(db, card):
			continue
		result = weibo_2_album.get(clearUrl(card['scheme']))
		if not db.existing.add(result.hash):
			continue
		yield result

def process(url, key):
	channels = db.subscription.channels(tele.bot, key)
	if not channels:
		return
	print(key)
	for item in getResults(url):
		for channel in channels:
			try:
				album_sender.send_v2(channel, item)
			except Exception as e:
				debug_group.send_message(item.url + ' ' + str(e))

@log_on_fail(debug_group)
def loopImp():
	removeOldFiles('tmp', day=0.1)
	sg.reset()
	db.reload()
	for keyword in db.subscription.keywords():
		content_id = urllib.request.pathname2url('100103type=1&q=' + keyword)
		url = 'https://m.weibo.cn/api/container/getIndex?containerid=%s&page_type=searchall' % content_id
		process(url, keyword)
	for user in db.subscription.users():
		url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=107603%s' \
			% (user, user)
		process(url, user)
	commitRepo(delay_minute=0)

def loop():
	loopImp()
	threading.Timer(60 * 10, loop).start() 

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.effective_message
	if not msg or not msg.text.startswith('/wb'):
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
	threading.Timer(1, loop).start() 
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(Filters.private & (~Filters.command), handleHelp))
	dp.add_handler(MessageHandler(Filters.private & Filters.command, handleStart), group=2)
	tele.start_polling()
	tele.idle()