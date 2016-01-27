# -*- coding: utf-8 -*-

import re
from datetime import date
from collections import OrderedDict

from django.conf import settings
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from open_facebook.exceptions import OpenFacebookException

from vkontakte_api.api import api_call as vk_api_call
from tweepy import Cursor, TweepError

from . forms import EngagementsForm, DetailForm, get_social
from . api import get_twitter_api


class IndexView(View, TemplateResponseMixin):

    template_name = 'engagements/index.html'

    twitter_headers = [
                u'Ссылка',
                u'Подписчики пользователя',
                u'Избранное',
                u'Ретвиты',
                # u'Комментарии',
    ]

    vk_headers = [
            u'Ссылка',
            u'Подписчики пользователя/группы',
            u'Лайки',
            u'Репосты',
            u'Комментарии',
    ]

    fb_headers = [
            u'Ссылка',
            u'Нравится страница',
            u'Говорят о странице',
            u'Лайки',
            u'Репосты',
            u'Комментарии',
    ]

    def get(self, request):
        return self.render_to_response({"form": EngagementsForm})

    def post(self, request):
        form = EngagementsForm(request.POST)
        if form.is_valid():
            links = form.cleaned_data['links']
            social = form.cleaned_data['socials']

            context = self.get_data(links, social)
            context['form'] = form
            return self.render_to_response(context)

        return self.render_to_response({"form": form})

    def get_data(self, links, social_name):
        links = links.splitlines()
        return {
            'headers': getattr(self, '%s_headers' % social_name),
            'rows': getattr(self, 'get_%s' % social_name)(links)
         }

    @staticmethod
    def get_twitter(links):
        rows = []

        for link in links:
            matches = re.match(r'^https?://twitter\.com/(.*?)/status/(\d+)$', link)
            link = '<a href="{0}">{0}</a>'.format(link)
            if matches:
                screen_name = matches.group(1)
                status_id = matches.group(2)

                api = get_twitter_api()

                try:
                    response = api.get_status(status_id)
                except TweepError as e:
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
                            e
                        ]
                    })
                    continue

                if not screen_name == response.user.screen_name:
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
                            'This tweet not belong this user',
                        ]
                    })
                    continue

                rows.append({
                    'status': 'ok',
                    'data': [
                        link,
                        response.author.followers_count,
                        response.favorite_count,
                        response.retweet_count,
                    ]
                })
            else:
                rows.append({
                    'status': 'error',
                    'data': [
                        link,
                        'Incorrect url',
                    ]
                })

        return rows

    @staticmethod
    def get_vk(links):
        rows = []

        for link in links:
            matches = re.match(r'^https?://vk\.com/wall(-?\d+_\d+)$', link)
            link = '<a href="{0}">{0}</a>'.format(link)
            if matches:
                post_id = matches.group(1)
                posts = vk_api_call('wall.getById', **{'posts': post_id, 'v': 5.27})
                if len(posts) == 0: # ERROR
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
                            'Record not found',
                        ]
                    })
                    continue

                post = posts[0]

                if post['owner_id'] > 0:
                    users = vk_api_call('users.get', **{'user_ids': post['owner_id'], 'fields': 'followers_count', 'v': 5.27})
                    owner = users[0]
                    subscribers_count = owner['followers_count']
                else:
                    group_id = -1 * post['owner_id']
                    groups = vk_api_call('groups.getById', **{'group_ids': group_id, 'fields': 'members_count', 'v': 5.44})
                    owner = groups[0]
                    subscribers_count = owner['members_count']

                rows.append({
                    'status': 'ok',
                    'data': [
                        link,
                        subscribers_count,
                        post['likes']['count'],
                        post['reposts']['count'],
                        post['comments']['count'],
                    ]
                })

            else:
                rows.append({
                    'status': 'error',
                    'data': [
                        link,
                        'Incorrect url',
                    ]
                })

        return rows

    @staticmethod
    def get_fb(links):
        from open_facebook import OpenFacebook
        graph = OpenFacebook(settings.FACEBOOK_API_ACCESS_TOKEN)

        rows = []

        for link in links:
            # https://www.facebook.com/Beelinerus/posts/588392457883231
            matches = re.match(r'^https?://www.facebook.com/(.*?)/posts/(\d+)$', link)
            link = '<a href="{0}">{0}</a>'.format(link)
            if matches:
                company_slug = matches.group(1)
                post_id = matches.group(2)

                try:
                    company = graph.get(company_slug, fields='id,likes,talking_about_count')
                except OpenFacebookException as e:
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
                            'Company not found',
                        ]
                    })
                    continue

                post_graph_id = '%s_%s' % (company['id'], post_id)
                try:
                    post = graph.get(post_graph_id, fields='comments.limit(0).summary(true),likes.limit(0).summary(true),shares.limit(0).summary(true)')
                except OpenFacebookException as e:
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
                            'Post not found',
                        ]
                    })
                    continue

                likes = ''
                shares = ''
                comments = ''

                if 'likes' in post:
                    likes = post['likes']['summary']['total_count']
                if 'shares' in post:
                    shares = post['shares']['count']
                if 'comments' in post:
                    comments = post['comments']['summary']['total_count']

                rows.append({
                    'status': 'ok',
                    'data': [
                        link,
                        company['likes'],
                        company['talking_about_count'],
                        likes,
                        shares,
                        comments,
                    ]
                })

            else:
                rows.append({
                    'status': 'error',
                    'data': [
                        link,
                        'Incorrect url',
                    ]
                })


        return rows


class DetailView(View, TemplateResponseMixin):
    template_name = 'engagements/detail.html'

    vk_detail_headers = OrderedDict([
        ('name', 'Имя'),
        ('url', 'Ссылка'),
        ('gender', 'Пол'),
        ('birth_date', 'Дата рождения'),
        ('age', 'Возраст'),
        ('country', 'Страна'),
        ('city', 'Город'),
        ('deactivated', 'deactivated'),
        ('member', 'Участник'), # or Follower
        ('like', 'Лайк'),
        ('share', 'Поделился'),
        ('comment', 'Комментарий'),
    ])

    fb_detail_headers = OrderedDict([
        ('name', 'Имя'),
        ('url', 'Ссылка'),
        ('like', 'Лайк'),
        ('share', 'Поделился'),
        ('comment', 'Комментарий'),
    ])

    twitter_detail_headers = OrderedDict([
        ('name', 'Имя'),
        ('url', 'Ссылка'),
        ('location', 'Location'),
        ('created_at', 'Аккаунт создан'),
        ('follower', 'Follower'),
        ('retweet', 'Retweet'),
    ])


    def get(self, request):
        return self.render_to_response({"form": DetailForm})

    def post(self, request):
        form = DetailForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data['link']

            context = self.get_data(link)
            context['form'] = form
            return self.render_to_response(context)

        return self.render_to_response({"form": form})

    def get_data(self, link):
        social_name = get_social(link)

        return {
            'headers': getattr(self, '%s_detail_headers' % social_name),
            'rows': getattr(self, 'get_%s_detail' % social_name)(link)
         }

    def age(self, birth_date):
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year
            # if today < my_birthday:
            if today < birth_date:
                age = age - 1
            return age
        else:
            return None

    # @staticmethod
    def vk_user(self, user):

        u = OrderedDict()
        for k in self.vk_detail_headers.keys():
            u[k] = ''

        u['name'] = user['last_name'] + ' ' + user['first_name']
        u['url'] = 'https://vk.com/id%s' % user['id']

        if 'deactivated' in user:
            u['deactivated'] = user['deactivated']

        if 'city' in user:
            u['city'] = user['city']['title']
        if 'country' in user:
            u['country'] = user['country']['title']

        if user["sex"] == 2:
            u["gender"] = "male"
        elif user["sex"] == 1:
            u["gender"] = "female"

        if 'bdate' in user:
            l = user["bdate"].split('.')
            if len(l) == 3:
                year = int(l[2])
                month = int(l[1])
                day = int(l[0])
                # u["birth_date"] = user["bdate"]
                birth_date = date(year, month, day)
                u["birth_date"] = birth_date.strftime("%d-%m-%Y")
                u["age"] = self.age(birth_date)

        return u


    # @staticmethod
    def get_vk_detail(self, link):
        from vkontakte_api.api import api_call, api_recursive_call

        # like https://vk.com/dev/likes.getList
        # share https://vk.com/dev/wall.getReposts
        # comment https://vk.com/dev/wall.getComments
        # members(followers) https://vk.com/dev/users.getFollowers

        rows = OrderedDict()

        matches = re.match(r'^https?://vk\.com/wall(-?\d+_\d+)$', link)
        if matches:
            post_id = matches.group(1)
            owner_id = post_id.split('_')[0]
            item_id = post_id.split('_')[1]

            # check
            posts = api_call('wall.getById', posts=post_id, v=5.44)
            if len(posts) == 0:
                rows['errors'] = 'Post not found'
                return rows

            # getting followers
            if int(owner_id) > 0:
                response = api_recursive_call('users.getFollowers', user_id=owner_id, fields='last_name', count=1000, v=5.44) # fields='last_name' added here to get 'deactivated' field
            else:
                group_id = -1 * int(owner_id)
                response = api_recursive_call('groups.getMembers', group_id=group_id, fields='last_name', count=1000, v=5.44) # fields='last_name' added here to get 'deactivated' field

            subscribers = {}
            subscribers_user_ids = []
            for u in response['items']:
                user_id = u['id']
                subscribers[user_id] = u
                subscribers_user_ids.append(user_id)

            # getting likes
            response = api_recursive_call('likes.getList', type='post', owner_id=owner_id, item_id=item_id, count=1000, v=5.44)
            likes_user_ids = response['items']

            # getting shares
            response = api_recursive_call('wall.getReposts', owner_id=owner_id, post_id=item_id, count=1000, v=5.44)
            shares = response['items']

            shares_user_ids = []
            for share in shares:
                user_id = share['from_id']
                shares_user_ids.append(user_id)

            # getting comments
            # count max 100
            response = api_recursive_call('wall.getComments', owner_id=owner_id, post_id=item_id, count=100, v=5.44)
            comments = response['items']

            comments_user_ids = []
            for comment in comments:
                user_id = comment['from_id']
                comments_user_ids.append(user_id)

            user_ids = set() # lets get unique set
            user_ids.update(subscribers_user_ids, likes_user_ids, shares_user_ids, comments_user_ids)
            user_ids_list = list(user_ids)

            start_pos = 0
            STEP = 350 # 350 is near maximum ids what method accepted, this number getting by experiment
            end_pos = STEP
            while start_pos < len(user_ids_list):
                slice = user_ids_list[start_pos:end_pos]

                user_ids_str = ','.join([str(id) for id in slice])
                response = api_call('users.get', user_ids=user_ids_str, fields='first_name, last_name, sex, bdate, country, city', v=5.8)

                for user in response:
                    u = self.vk_user(user)
                    user_id = user['id']

                    if user_id in subscribers_user_ids:
                        u['member'] = 1
                        if 'deactivated' in subscribers[user_id]:
                            u['deactivated'] = subscribers[user_id]['deactivated']
                    if user_id in likes_user_ids:
                        u['like'] = 1
                    if user_id in shares_user_ids:
                        u['share'] = 1
                    if user_id in comments_user_ids:
                        u['comment'] = comments_user_ids.count(user_id)

                    rows[user_id] = u

                # increse
                start_pos += STEP
                end_pos += STEP
        else:
            rows['errors'] = 'Invalid post link'

        return rows

    def fb_user(self, user):
        u = OrderedDict()
        for k in self.fb_detail_headers.keys():
            u[k] = ''

        u['name'] = user['name']
        u['url'] = 'https://www.facebook.com/profile.php?id=%s' % user['id']
        u['comment'] = 0

        return u

    def get_fb_detail(self, link):
        from open_facebook import OpenFacebook
        from . utils import recursive_graph_call

        graph = OpenFacebook(settings.FACEBOOK_API_ACCESS_TOKEN)

        rows = {}

        matches = re.match(r'^https?://www.facebook.com/(.*?)/posts/(\d+)$', link)
        if matches:
            company_slug = matches.group(1)
            post_id = matches.group(2)

            company = graph.get(company_slug, fields='id')

            post_graph_id = '%s_%s' % (company['id'], post_id)

            # getting likes
            response = recursive_graph_call(post_graph_id + '/likes', limit=500)

            for user in response['data']:
                u = self.fb_user(user)
                u['like'] = 1
                rows[user['id']] = u

            # getting shares
            response = recursive_graph_call(post_graph_id + '/sharedposts', fields='from', limit=500)

            for share in response['data']:
                user = share['from']

                if user['id'] not in rows:
                    u = self.fb_user(user)
                    u['share'] = 1
                    rows[user['id']] = u
                else:
                    rows[user['id']]['share'] = 1

            # getting comments
            response = recursive_graph_call(post_graph_id + '/comments', fields='from', limit=500)

            for comment in response['data']:
                user = comment['from']

                if user['id'] not in rows:
                    u = self.fb_user(user)
                    u['comment'] += 1
                    rows[user['id']] = u
                else:
                    rows[user['id']]['comment'] += 1
        else:
            rows['errors'] = 'Invalid post link'

        return rows

    def twitter_user(self, user):
        u = OrderedDict()
        for k in self.twitter_detail_headers.keys():
            u[k] = ''

        u['name'] = user.name
        u['url'] = 'https://twitter.com/%s' % user.screen_name
        u['location'] = user.location
        u['created_at'] = user.created_at.strftime("%d-%m-%Y %H:%M")

        return u

    def get_twitter_detail(self, link):
        rows = {}

        matches = re.match(r'^https?://twitter.com/(.*?)/status/(\d+)$', link)
        if matches:
            screen_name = matches.group(1)
            status_id = matches.group(2)

            api = get_twitter_api()

            try:
                response = api.get_status(status_id)
            except TweepError as e:
                rows['errors'] = e
                return rows

            if not screen_name == response.user.screen_name:
                rows['errors'] = 'This tweet not belong this user'
                return rows

            response = Cursor(api.followers, screen_name=screen_name, count=200).items()
            for user in response:
                u = self.twitter_user(user)
                u['follower'] = 1
                rows[user.id] = u

            response = api.retweets(status_id)
            for s in response:
                user = s.user

                if user.id not in rows:
                    u = self.twitter_user(user)
                    u['retweet'] = 1
                    rows[user.id] = u
                else:
                    rows[user.id]['retweet'] = 1
        else:
            rows['errors'] = 'Invalid post link'

        return rows
