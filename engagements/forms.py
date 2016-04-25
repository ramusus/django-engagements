# -*- coding: utf-8 -*-
from django import forms
# from django.core.exceptions import ValidationError


# def get_social(link):
#     SOCIALS = {'twitter': 'https://twitter.com',
#                'vk': 'https://vk.com',
#                'fb': 'https://www.facebook.com',
#     }
#     for social_name, social_url in SOCIALS.items():
#         if link.startswith(social_url):
#             return social_name
#
#
# def social_validator(value):
#     social = get_social(value)
#
#     if not social:
#         raise ValidationError('%s This social net is not supported' % value)


class EngagementsForm(forms.Form):
    links = forms.CharField(label=u'Ссылки', required=True,
                            widget=forms.Textarea(attrs={
                                'class': 'form-control',
                                'rows': '5',
                                'style': 'width: 100% !important;'
                            }))

    SOCIALS = (('twitter', 'Twitter'), ('vk', 'Vkontakte'), ('fb', 'Facebook'),)
    socials = forms.ChoiceField(label=u'Соц. сеть', widget=forms.RadioSelect, choices=SOCIALS, required=True)


class DetailForm(EngagementsForm):
    pass
