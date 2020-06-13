import tweepy
import threading

# it seems steam does not need auth?

class UserUpdateListender(tweepy.StreamListener):
	def __init__(self, db):
		self.db = db
		super().__init__()

	def on_data(self, data):
		print(data)

	def on_error(self, status_code):
		print('on_error = ' + str(status_code))

class KeyUpdateListender(tweepy.StreamListener):
	def __init__(self, db):
		self.db = db
		super().__init__()

	def on_data(self, data):
		print(data)

	def on_error(self, status_code):
		print('on_error = ' + str(status_code))

class Stream(object):
	def __init__(self, db, twitterApi):
		self.db = db
		self.user_stream = None
		self.key_stream = None
		self.twitterApi = twitterApi
		self.reload()

	def reloadSync(self):
		if self.user_stream and not self.user_stream.running:
			self.user_stream.disconnect()
			self.user_stream = None
		if not self.user_stream:
			self.user_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=UserUpdateListender(self.db))
			self.user_stream.filter(follow=self.db.sub.users())

		if self.key_stream and not self.key_stream.running:
			self.key_stream.disconnect()
			self.key_stream = None
		if not self.key_stream:
			self.key_stream = tweepy.Stream(auth=self.twitterApi.auth, listener=KeyUpdateListender(self.db))
			self.key_stream.filter(track=self.db.sub.keys()) # need two stream

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
