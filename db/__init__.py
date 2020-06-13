import os
import yaml
from telegram_util import commitRepo

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
			return
		self.items.add(x)
		with open(self.fn, 'a') as f:
			f.write('\n' + x)
		commitRepo(delay_minute=0)

	def remove(self, x):
		try:
			self.items.remove(x)
		except:
			pass
		with open(self.fn, 'w') as f:
			f.write('\n'.join(self.items))
		commitRepo(delay_minute=0)

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
				yield bot.get_chat(chat_id)
			except:
				...

def isInt(text):
	try:
		int(text)
		return True
	except:
		return False

class Subscription(object):
	def __init__(self):
		with open('db/user_sub') as f:
			self.user_sub = yaml.load(f, Loader=yaml.FullLoader)
		with open('db/key_sub') as f:
			self.key_sub = yaml.load(f, Loader=yaml.FullLoader)

	def add(self, chat_id, text, twitterApi):
		if not text:
			return
		user_id = None
		if '/' in text or isInt(text):
			user_id = getUserId(text, twitterApi)
		if user_id:
			tryAdd(self.user_sub, chat_id, user_id)
		else:
			tryAdd(self.key_sub, chat_id, text)
		self.save()

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

class DB(object):
	def __init__(self):
		self.reload()

	def reload(self):
		self.queue = DBItem('queue')
		self.blacklist = DBItem('blacklist')
		self.popularlist = DBItem('popularlist')
		self.sub = Subscription()
