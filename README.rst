==================
Django Engagements
==================

Django tool to collect engagements (like comments, shares or likes) for social networks.

Quick start
-----------

First of all, read the installation instructions here:
https://github.com/ramusus/django-twitter-api,
https://github.com/ramusus/django-vkontakte-api

Then add this app to your INSTALLED_APPS setting::

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'vkontakte_api',
        'engagements',
    )

Include the engagements URLs in your project::

    url(r'^engagements/', include('engagements.urls')),
