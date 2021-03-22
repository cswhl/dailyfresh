from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
# from order.models import


# Create your views here.

# /order/place
class OrderPlaceView(View):
    '''提交订单页面显示'''

    def post(self, request):
        '''提交订单页面'''

        # 获取用户
        user = request.user

        # 获取购买的商品id

        # 校验参数

        # 获取购买的商品

        # 业务处理：

        return render(request, 'place_order.html')
