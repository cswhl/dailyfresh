from django.conf.urls import url
from order.views import OrderPlaceView

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'), # 下订单页面
]
