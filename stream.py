import tweepy
import threading

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

class Stream(object):
	def __init__(self, db):
		self.db = db
		self.user_stream = None
		self.key_stream = None
		self.reload()

	def reloadSync(self):
		if self.user_stream and not self.user_stream.running::
			self.user_stream.disconnect()
			self.user_stream = None
		if not self.user_stream:
			self.user_stream = tweepy.Stream(auth=twitterApi.auth, listener=UserUpdateListender(self.db))
			self.user_stream.filter(follow=db.getUsers())

		if self.key_stream and not self.key_stream.running:
			self.key_stream.disconnect()
			self.key_stream = None
		if not self.key_stream:
			self.key_stream = tweepy.Stream(auth=twitterApi.auth, listener=KeyUpdateListender(self.db))
			self.key_stream.track(follow=db.getKeys()) # need two stream

	def reload(self):
		threading.Thread(target=self.reloadSync).start()
