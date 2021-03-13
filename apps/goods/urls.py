from django.conf.urls import url
from goods.views import IndexView, DetailView

urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^detail/(\d+)$', DetailView.as_view(), name='detail'),
]
