from django.conf import settings

import tweepy


TWITTER_CLIENT_ID = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_ID', None)
TWITTER_CLIENT_SECRET = getattr(settings, 'OAUTH_TOKENS_TWITTER_CLIENT_SECRET', None)


def get_twitter_api():
    auth = tweepy.OAuthHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True, retry_count=3, retry_delay=1, retry_errors=set([401, 404, 500, 503]))
