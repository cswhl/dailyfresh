from django.conf.urls import url
from cart.views import CartAddView, CartInfoView, CartUpdateView

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add'),  # 购物车商品添加
    url(r'^$', CartInfoView.as_view(), name='show'),  # 购物车页显示
    url(r'^update$', CartUpdateView.as_view(), name='update'),  # 购物车页显示
]
