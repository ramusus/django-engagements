# -*- coding: utf-8 -*-

import re
from datetime import date
from collections import OrderedDict

from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from twitter_api.api import api_call, TwitterError
from vkontakte_api.api import api_call as vk_api_call

from .forms import EngagementsForm, DetailForm


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
                status_id = matches.group(2)
                try:
                    response = api_call('get_status', status_id)
                except TwitterError:
                    rows.append({
                        'status': 'error',
                        'data': [
                            link,
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


    def get(self, request):
        return self.render_to_response({"form": DetailForm})

    def post(self, request):
        form = DetailForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data['link']
            print link

            context = self.get_data(link)
            context['form'] = form
            return self.render_to_response(context)

        return self.render_to_response({"form": form})

    def get_social(self, link):
        SOCIALS = {'twitter': 'https://twitter.com',
                   'vk': 'https://vk.com',
        }
        for social_name, social_url in SOCIALS.items():
            if link.startswith(social_url):
                return social_name

    def get_data(self, link):
        social_name = self.get_social(link)
        print social_name

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
        # print user

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

        # print u
        return u



    # @staticmethod
    def get_vk_detail(self, link):
        from vkontakte_api.api import api_call

        # like https://vk.com/dev/likes.getList
        # share https://vk.com/dev/wall.getReposts
        # comment https://vk.com/dev/wall.getComments
        # members(followers) https://vk.com/dev/users.getFollowers

        rows = OrderedDict()

        matches = re.match(r'^https?://vk\.com/wall(-?\d+_\d+)$', link)
        # link = '<a href="{0}">{0}</a>'.format(link)
        if matches:
            post_id = matches.group(1)
            owner_id = post_id.split('_')[0]
            item_id = post_id.split('_')[1]
            # print owner_id

            # getting followers
            if owner_id > 0:
                response = api_call('users.getFollowers', user_id=owner_id, fields='last_name', v=5.44) # fields='last_name' added here to get 'deactivated' field
                subscribers = {}
                subscribers_user_ids = []

                for u in response['items']:
                    user_id = u['id']
                    subscribers[user_id] = u
                    subscribers_user_ids.append(user_id)

                print "______________________"
                print response['count']

            else:
                pass

            # getting likes
            response = api_call('likes.getList', type='post', owner_id=owner_id, item_id=item_id, v=5.44)
            likes_user_ids = response['items']

            # getting shares
            response = api_call('wall.getReposts', owner_id=owner_id, post_id=item_id, v=5.44)
            shares = response['items']

            shares_user_ids = []
            for share in shares:
                user_id = share['from_id']
                shares_user_ids.append(user_id)

            # getting comments
            # count max 100
            response = api_call('wall.getComments', owner_id=owner_id, post_id=item_id, v=5.44)
            comments = response['items']

            comments_user_ids = []
            for comment in comments:
                user_id = comment['from_id']
                shares_user_ids.append(user_id)

            # print subscribers_user_ids
            # print likes_user_ids
            # print shares_user_ids
            # print comments_user_ids

            print len(subscribers_user_ids)
            print len(likes_user_ids)
            print len(shares_user_ids)
            print len(comments_user_ids)

            user_ids = set()
            user_ids.update(subscribers_user_ids, likes_user_ids, shares_user_ids, comments_user_ids)
            user_ids_str = ','.join([str(id) for id in user_ids])

            response = api_call('users.get', user_ids=user_ids_str, fields='first_name, last_name, sex, bdate, country, city', v=5.44)
            print response

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
                    u['comment'] = 1

                rows[user_id] = u

            return rows
    
    
    
