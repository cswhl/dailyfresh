from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'), # 下订单页面
    url(r'^commit$', OrderCommitView.as_view(), name='commit'), # 订单提交
]
