import requests
from vkontakte_api.api import VkontakteApi

SECURE_API_URL = 'https://api.vk.com/method/'
NO_TOKEN_METHODS = [
    'users.get',
    'users.search',
    'users.getFollowers',

    'groups.get',
    'groups.getById',
    'groups.getMembers',

    'wall.get',
    'wall.getById',
    'wall.search',
    'wall.getReposts',
    'wall.getComments',

    'photos.get',
    'photos.getAlbums',
    'photos.getProfile',
    'photos.getById',

    'likes.getList',
]


class ApiCallError(Exception):
    def __init__(self, value):
          self.value = value
    def __str__(self):
         return repr(self.value)


def api_call(method, *args, **kwargs):

    if method in NO_TOKEN_METHODS:
        url = SECURE_API_URL + method # 'https://api.vk.com/method/users.get'
        r = requests.get(url, params=kwargs)
        if r.status_code == 200:
            return r.json()["response"]
        else:
            raise ApiCallError(r.content)
    else:
        api = VkontakteApi()
        return api.call(method, *args, **kwargs)


def api_recursive_call(method, *args, **kwargs):

    if 'offset' not in kwargs:
        kwargs['offset'] = 0
    if 'count' not in kwargs:
        kwargs['count'] = 100

    response = {}
    while True:
        # print kwargs['offset']
        r = api_call(method, *args, **kwargs)
        kwargs['offset']= kwargs['count']

        if not response: # first call
            response = r
        else:
            response['items']= r['items']

        if 'count' in response:
            if len(response['items']) >= response['count']:
                # print "items: %s, count: %s" % (len(response['items']), response['count'])
                break
        # not all method return count
        if len(r['items']) == 0:
            # print "0 items"
            break

    return response
