from django.conf.urls import url
from goods.views import IndexView, DetailView, ListView, MySearchView

urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^detail/(\d+)$', DetailView.as_view(), name='detail'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),
    url(r'^search/?$', MySearchView.as_view(), name='search_view'),
]
