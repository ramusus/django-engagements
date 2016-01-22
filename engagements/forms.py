# -*- coding: utf-8 -*-
from django import forms


class EngagementsForm(forms.Form):
    links = forms.CharField(label=u'Ссылки', required=True,
                            widget=forms.Textarea(attrs={
                                'class': 'form-control',
                                'rows': '5',
                                'style': 'width: 100% !important;'
                            }))

    SOCIALS = (('twitter', 'Twitter'), ('vk', 'Vkontakte'), ('fb', 'Facebook'),)
    socials = forms.ChoiceField(label=u'Соц. сеть', widget=forms.RadioSelect, choices=SOCIALS, required=True)



class DetailForm(forms.Form):
    link = forms.CharField(label=u'Ссылка', required=True,
                            widget=forms.TextInput(attrs={
                                'class': 'form-control',
                                'style': 'width: 100% !important;'
                            }))
