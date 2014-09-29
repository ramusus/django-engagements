==================
Django Engagements
==================

Django tool to collect engagements (like comments, shares or likes) for social networks.

Quick start
-----------

First of all, read the installation instructions here: https://github.com/ramusus/django-twitter-api.
Then add this app to your INSTALLED_APPS setting::

    INSTALLED_APPS = (
        ...
        'engagements',
    )

Include the engagements URLs in your project::

    url(r'^engagements/', include('engagements.urls')),
