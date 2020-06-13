import tweepy
import threading
import twitter_2_album
import yaml
import album_sender
import time
from telegram_util import matchKey

cache = {}

def getTid(data):
	if 'id' in data:
		return data['id']
	return data['delete']['status']['id']

def getAlbum(data):
	tid = getTid(data)
	if tid in cache:
		for r in cache[tid]:
			r.delete()
	cache[tid] = []
	if 'delete' in data:
		return tid, None
	return tid, twitter_2_album.get(str(tid))

class UserUpdateListender(tweepy.StreamListener):
	def __init__(self, db, bot):
		self.db = db
		self.bot = bot
		super().__init__()

	def on_data(self, data):
		data = yaml.load(data, Loader=yaml.FullLoader)
		tid, r = getAlbum(data)
		if not r:
			return
		for channel in self.db.sub.channelsForUser(self.bot, data['user']['id']):
			cache[tid] += album_sender.send_v2(channel, r)

	def on_error(self, status_code):
		return

def getCount(data):
	try:
		data = data['retweeted_status']
		return int(data.get('retweet_count')) + int(
			data.get('favorite_count'))
	except Exception as e:
		return 0

def isRich(data):
	return 'expanded_url' in str(data)

def shouldProcess(data, db):
	if 'delete' in data:
		return True
	if matchKey(str(data), db.blacklist.items):
		return False
	bar = 100000
	if matchKey(str(data), db.popularlist.items):
		bar *= 10
	if isRich(data):
		bar /= 10
	return getCount(data) > bar

class KeyUpdateListender(tweepy.StreamListener):
	def __init__(self, db, bot):
		self.db = db
		self.bot = bot
		super().__init__()

	def on_data(self, data):
		data = yaml.load(data, Loader=yaml.FullLoader)
		if not shouldProcess(data, self.db):
			return
		if not self.db.existing.add(data['retweeted_status']['id']):
			return
		tid, r = getAlbum(data)
		if not r:
			return
		for chat_id in self.db.sub.key_sub:
			try:
				channel = self.bot.get_chat(chat_id)
			except:
				continue
			if matchKey(r.cap, self.db.sub.key_sub.get(chat_id, [])):
				cache[tid] += album_sender.send_v2(channel, r)
				time.sleep(10)

	def on_error(self, status_code):
		return

class Stream(object):
	def __init__(self, db, twitterApi, bot):
		self.db = db
		self.user_stream = None
		self.key_stream = None
		self.twitterApi = twitterApi
		self.bot = bot
		self.reload()

	def reloadSync(self):
		if self.user_stream and not self.user_stream.running:
			self.user_stream.disconnect()
			self.user_stream = None
		if not self.user_stream:
			self.user_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=UserUpdateListender(self.db, self.bot))
			self.user_stream.filter(follow=self.db.sub.users())

		if self.key_stream and not self.key_stream.running:
			self.key_stream.disconnect()
			self.key_stream = None
		if not self.key_stream:
			self.key_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=KeyUpdateListender(self.db, self.bot))
			self.key_stream.filter(track=self.db.sub.keys()) # need two stream

	def forceReload(self):
		if self.user_stream:
			self.user_stream.disconnect()
			self.user_stream = None
		if self.key_stream:
			self.key_stream.disconnect()
			self.key_stream = None
		self.reload()

	def reload(self):
		threading.Timer(0, self.reloadSync).start()
