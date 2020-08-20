import yaml
from telegram_util import commitRepo, isInt, matchKey
import plain_db
from common import bot, twitterApi

def getUserId(text):
	try:
		screenname = text.split('?')[0].strip('@').strip('/').split('/')[-1]
		user = twitterApi.get_user(screenname)
		return user.id
	except:
		...

def getMatches(text):
	if not text:
		return []
	if matchKey(text, ['/', '@']) or isInt(text):
		user_id = getUserId(text)
		if user_id and isInt(text):
			return [user_id]
		if user_id:
			return [user_id, text]
	return [text]

class Subscription(object):
	def __init__(self):
		with open('db/subscription') as f:
			self._db = yaml.load(f, Loader=yaml.FullLoader)

	def add(self, chat_id, text):
		matches = getMatches(text)
		if not matches:
			return False
		text = matches[0]
		self._db[chat_id] = self._db.get(chat_id, [])
		if text in self._db[chat_id]:
			return False
		self._db[chat_id].append(text)
		self.save()
		return True

	def remove(self, chat_id, text):
		matches = getMatches(text)
		for match in matches:
			if match in self._db.get(chat_id, []):
				self._db[chat_id].remove(match)
				self.save()
				return True
		return False

	def getSubscription(self, chat_id):
		result = []
		for text in self._db.get(chat_id, []):
			user = twitterApi.get_user(text)
			if user:
				item = '[%s](%s)' % (user.name, 
					'https://twitter.com/' + str(user.screen_name))
				result = [item] + result
			else:
				result.append(text)
		return 'subscriptions: ' + ' '.join(result)

	def getChats(self, text):
		for chat_id in self._db:
			if text in self._db[chat_id]: # verified, this works
				try:
					yield bot.get_chat(chat_id)
				except:
					...

	def save(self):
		with open('db/subscription', 'w') as f:
			f.write(yaml.dump(self._db, sort_keys=True, indent=2, allow_unicode=True))
		# commitRepo(delay_minute=0) # testing

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
			subscription.add(chat_id, str(item))

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