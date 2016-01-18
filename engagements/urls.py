from django.conf.urls import patterns, url
from views import IndexView, DetailView

urlpatterns = patterns('',
    url(r"^$", IndexView.as_view(), name="engagements_form"),
    url(r"^detail/$", DetailView.as_view(), name="detail_view"),
)
