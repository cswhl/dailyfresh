from django.conf.urls import url
from cart.views import CartAddView

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add'), # 购物车商品添加
]
