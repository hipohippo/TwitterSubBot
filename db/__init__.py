import os
import yaml
import threading
import time
from telegram_util import commitRepo
import uuid

def getFile(name):
	fn = 'db/' + name
	os.system('touch ' + fn)
	with open(fn) as f:
		return set([x.strip() for x in f.readlines() if x.strip()])

class DBItem(object):
	def __init__(self, name):
		self.items = getFile(name)
		self.fn = 'db/' + name

	def add(self, x):
		x = str(x).strip()
		if not x or x in self.items:
			return False
		self.items.add(x)
		with open(self.fn, 'a') as f:
			f.write('\n' + x)
		return True

	def contains(self, x):
		x = str(x).strip()
		return x in self.items

def getUserId(text, twitterApi):
	try:
		screenname = text.strip('/').split('/')[-1]
		user = twitterApi.get_user(screenname)
		return user.id
	except:
		...

def tryRemove(sub_list, text)
	try:
		sub_list.remove(text)
	except:
		...

def getSubscriptions(sub):
	result = set()
	for chat_id in sub:
		for item in sub.get(chat_id, []):
			result.add(item)
	return result

class Subscription(object):
	def __init__(self):
		with open('db/user_sub') as f:
			self.user_sub = yaml.load(f, Loader=yaml.FullLoader)
		with open('db/key_sub') as f:
			self.key_sub = yaml.load(f, Loader=yaml.FullLoader)

	def add(self, chat_id, text, twitterApi):
		if not text:
			return
		user_id = getUserId(text, twitterApi)
		if user_id:
			self.user_sub[chat_id] = self.user_sub.get(chat_id, []) + [user_id]
			return
		self.key_sub[chat_id] = self.key_sub.get(chat_id, []) + [text]
		self.save()

	def remove(self, chat_id, text):
		user_id = getUserId(text, twitterApi)
		if user_id:
			tryRemove(self.user_sub.get(chat_id), user_id)
		else:
			tryRemove(self.key_sub.get(chat_id), text)

	def get(self, chat_id):
		return '当前订阅：' + ' '.join(self.sub.get(chat_id, []))


	def keywords(self):
		getSubscriptions(self.key_sub)

	def users(self):
		getSubscriptions(self.user_sub)

	def channels(self, bot, text):
		for chat_id in self.sub:
			if text in self.sub.get(chat_id, []):
				try:
					yield bot.get_chat(chat_id)
				except:
					...

	def save(self):
		with open('db/subscription', 'w') as f:
			f.write(yaml.dump(self.sub, sort_keys=True, indent=2, allow_unicode=True))
		commitRepo(delay_minute=0)

class Existing(object):
	def __init__(self):
		current_fn = 'existing_' + str(uuid.getnode())
		self.current = DBItem(current_fn)
		self.all = []
		for fn in os.listdir('db'):
			if fn.startswith('existing') and fn != current_fn:
				self.all.append(DBItem(fn))

	def add(self, item):
		for dbitem in self.all:
			if dbitem.contains(item):
				return False
		return self.current.add(item)

class DB(object):
	def __init__(self):
		self.reload()

	def reload(self):
		self.existing = Existing()
		self.blacklist = DBItem('blacklist')
		self.popularlist = DBItem('popularlist')
		self.subscription = Subscription()
