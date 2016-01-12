# -*- coding: utf-8 -*-

import re

from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from twitter_api.api import api_call, TwitterError
from vkontakte_api.api import api_call

from .forms import EngagementsForm


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
                posts = api_call('wall.getById', **{'posts': post_id, 'v': 5.27})
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
                    users = api_call('users.get', **{'user_ids': post['owner_id'], 'fields': 'followers_count', 'v': 5.27})
                    owner = users[0]
                    subscribers_count = owner['followers_count']
                else:
                    group_id = -1 * post['owner_id']
                    groups = api_call('groups.getById', **{'group_ids': group_id, 'fields': 'members_count', 'v': 5.44})
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
