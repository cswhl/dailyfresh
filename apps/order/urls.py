from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, OrderCheckView, OrderCommentView

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'), # 下订单页面
    url(r'^commit$', OrderCommitView.as_view(), name='commit'), # 订单提交
    url(r'^pay$', OrderPayView.as_view(), name='pay'), # 支付
    url(r'^check$', OrderCheckView.as_view(), name='check'), # 查询支付结果
    url(r'^comment/(?P<order_id>\d+)$', OrderCommentView.as_view(), name='comment'), # 订单评论页面
]
