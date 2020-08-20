import os
import yaml
from telegram_util import commitRepo, isInt, matchKey
import plain_db
from .common import bot, debug_group, twitterApi

def getUserId(text, twitterApi):
	try:
		screenname = text.strip('/').split('/')[-1]
		user = twitterApi.get_user(screenname)
		return user.id
	except:
		...

def tryRemove(sub_list, text):
	try:
		sub_list.remove(text)
	except:
		...

def tryAdd(sub, chat_id, text):
	if chat_id not in sub:
		sub[chat_id] = []
	if text in sub[chat_id]:
		return
	sub[chat_id].append(text)

def getSubscriptions(sub):
	result = set()
	for chat_id in sub:
		for item in sub.get(chat_id, []):
			result.add(item)
	return list(result)

def getChannels(bot, sub, text):
	for chat_id in sub:
		if text in sub.get(chat_id, []):
			try:
				channel = bot.get_chat(chat_id)
				yield channel
			except:
				...

class Subscription(object):
	def __init__(self):
		with open('db/subscription') as f:
			self._db = yaml.load(f, Loader=yaml.FullLoader)

	def add(self, chat_id, text):
		if not text:
			return
		user_id = None
		if matchKey(text, ['/', '@']) or isInt(text):
			user_id = getUserId(text)
		text = user_id or text
		self._db[chat_id] = self._db.get(chat_id, [])
		if text in self._db[chat_id]:
			return False
		self._db[chat_id].remove(text)
		# commitRepo() # testing
		return True

	def remove(self, chat_id, text, twitterApi):
		user_id = getUserId(text, twitterApi)
		if user_id:
			tryRemove(self.user_sub.get(chat_id), user_id)
		tryRemove(self.key_sub.get(chat_id), text)
		self.save()

	def get(self, chat_id, twitterApi):
		result = []
		for user_id in self.user_sub.get(chat_id, []):
			user = twitterApi.get_user(user_id)
			if user:
				result.append('[%s](%s)' % (user.name, 'https://twitter.com/' + str(user.screen_name)))
		return 'subscriptions: ' + ' '.join(result + self.key_sub.get(chat_id, []))

	def keys(self):
		return getSubscriptions(self.key_sub)

	def users(self):
		return [str(x) for x in getSubscriptions(self.user_sub)]

	def channelsForUser(self, bot, user_id):
		return getChannels(bot, self.user_sub, user_id)

	def save(self):
		with open('db/user_sub', 'w') as f:
			f.write(yaml.dump(self.user_sub, sort_keys=True, indent=2, allow_unicode=True))
		with open('db/key_sub', 'w') as f:
			f.write(yaml.dump(self.key_sub, sort_keys=True, indent=2, allow_unicode=True))
		commitRepo(delay_minute=0)

def hasPermission(chat_id):
	try:
		r = bot.send_message(chat_id, 'test')
		r.delete()
		return True
	except:
		return False

def batchAdd(old_dict):
	for chat_id in old_dict:
		if not hasPermission(chat_id):
			continue
		items = old_dict.get(chat_id)
		for item in items:
			subscription.add(chat_id, item)

def migrate():
	with open('db/user_sub') as f:
		user_sub = yaml.load(f, Loader=yaml.FullLoader)
	with open('db/key_sub') as f:
		key_sub = yaml.load(f, Loader=yaml.FullLoader)
	batchAdd(key_sub)
	batchAdd(user_sub)
	
blocklist = plain_db.loadKeyOnlyDB('blocklist')
popularlist = plain_db.loadKeyOnlyDB('popularlist')
existing = plain_db.loadKeyOnlyDB('existing')
subscription = Subscription()