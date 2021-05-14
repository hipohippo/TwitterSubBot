import yaml
import tweepy
from telegram.ext import Updater 

with open('CREDENTIALS') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot'], use_context=True)  # @twitter_send_bot
bot = tele.bot
debug_group = bot.get_chat(420074357)
logger = bot.get_chat(-1001475764085)

auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
twitterApi = tweepy.API(auth)