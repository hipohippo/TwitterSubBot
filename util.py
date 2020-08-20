from telegram_util import matchKey
from db import blocklist, subcription

def getHash(status):
	retweeted_id = status._json.get('retweeted_status', {}).get('id')
	if retweeted:
		return retweeted
	return status.id

def getCountInner(data):
	try:
		return int(data.get('retweet_count')) + int(
			data.get('favorite_count') + 
			int(data.get('retweet_count', 0)) +
			int(data.get('favorite_count', 0)))
	except Exception as e:
		return 0

def getCount(status):
	data = status._json
	return getCountInner(data.get('retweeted_status', {})) / 3 + getCountInner(data)

def isRich(data):
	return 'expanded_url' in str(data)

def shouldProcess(data, db):
	if 'delete' in data:
		return True
	if matchKey(str(data), db.blocklist.items):
		return False
	bar = 1000000
	if matchKey(str(data), db.popularlist.items):
		bar *= 10
	if isRich(data):
		bar /= 10
	return getCount(data) > bar

def shouldApplyFilter(chat_id, key):
	return not isinstance(key, int):
		return subscription.filterOnUser(chat_id)
	return subscription.filterOnKey(chat_id)

def passKeyFilter(card):
	if matchKey(str(card), popularlist.items()):
		return weiboo.getCount(card) > 10000
	return weiboo.getCount(card) > 1000

def passMasterFilter(data):
	if matchKey(str(data), db.blocklist.items):
		return False
	return True

def tooOld(data): # for migration purpose
	return data.get('timestamp_ms', 0) < 1597521833000

def passFilter(channel, status, key):
	data = status._json
	if tooOld(data): # for hash migration
		return False
	chat_id = channel.id
	if key not in subscription._db.get(chat_id, []):
		return False
	if (subscription.hasMasterFilter(chat_id) and 
		not passMasterFilter(data)):
		return False
	if not isinstance(key, int) and not passKeyFilter(data):
		return False
	return True