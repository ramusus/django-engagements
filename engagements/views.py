# -*- coding: utf-8 -*-

import re

from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from twitter_api.api import api_call, TwitterError

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
                    ]
                })

        return rows
