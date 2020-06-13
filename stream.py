import tweepy
import threading
import twitter_2_album
import yaml
import album_sender

cache = {}

def getTid(data):
	if 'id' in data:
		return data['id']
	return data['delete']['id']


class UserUpdateListender(tweepy.StreamListener):
	def __init__(self, db, bot):
		self.db = db
		self.bot = bot
		super().__init__()
		print('UserUpdateListender start')

	def on_data(self, data):
		print(data)
		data = yaml.load(data, Loader=yaml.FullLoader)
		tid = getTid(data)
		if tid in cache:
			for r in cache[tid]:
				r.delete()
		cache[tid] = []
		if 'delete' in data:
			return
		r = twitter_2_album.get(str(tid))
		for channel in self.db.sub.channelsForUser(self.bot, data['user']['id']):
			cache[tid] += album_sender.send_v2(channel, r)

	def on_error(self, status_code):
		return

class KeyUpdateListender(tweepy.StreamListener):
	def __init__(self, db, bot):
		self.db = db
		self.bot = bot
		super().__init__()

	def on_data(self, data):
		...

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
			print(4)
			self.user_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=UserUpdateListender(self.db, self.bot))
			self.user_stream.filter(follow=self.db.sub.users())

		# if self.key_stream and not self.key_stream.running:
		# 	self.key_stream.disconnect()
		# 	self.key_stream = None
		# if not self.key_stream:
		# 	self.key_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=KeyUpdateListender(self.db, self.bot))
		# 	self.key_stream.filter(track=self.db.sub.keys()) # need two stream

	def forceReload(self):
		# TODO: may need to put this into thread
		if self.user_stream:
			self.user_stream.disconnect()
			self.user_stream = None
		if self.key_stream:
			self.key_stream.disconnect()
			self.key_stream = None
		self.reload()

	def reload(self):
		threading.Timer(0, self.reloadSync).start()
