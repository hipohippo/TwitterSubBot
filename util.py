from telegram_util import matchKey
from db import blocklist, subscription

def getHash(status):
	retweeted_id = status._json.get('retweeted_status', {}).get('id')
	if retweeted_id:
		return retweeted_id
	return status.id

def getCountInner(data):
	try:
		return int(data.get('retweet_count')) + int(
			data.get('favorite_count') + 
			int(data.get('retweet_count', 0)) +
			int(data.get('favorite_count', 0)))
	except Exception as e:
		return 0

def getCount(data):
	count = (getCountInner(data.get('retweeted_status', {})) / 3 + 
		getCountInner(data))
	return count

def passKeyFilter(data):
	return getCount(data) > 100000

def passMasterFilter(data):
	if matchKey(str(data), blocklist.items()):
		return False
	return True

def passFilter(channel, status, key):
	data = status._json
	chat_id = channel.id
	if key not in subscription._db.get(chat_id, []):
		return False
	if (subscription.hasMasterFilter(chat_id) and 
		not passMasterFilter(data)):
		return False
	if key == 'hometimeline':
		return getCount(data) > 200
	if not isinstance(key, int) and not passKeyFilter(data):
		return False
	if subscription.hasUserFilter(chat_id):
		return getCount(data) > 200
	return True