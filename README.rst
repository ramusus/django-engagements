==================
Django Engagements
==================

Django tool for collection engagements (like comments or shares) for social networks.

Quick start
-----------

First of all, read installation instructions from this link
https://github.com/ramusus/django-twitter-api
Then add this app to your INSTALLED_APPS setting::

    INSTALLED_APPS = (
        ...
        'engagements',
    )

Include the engagements URLs in your project::

    url(r'^engagements/', include('engagements.urls')),
