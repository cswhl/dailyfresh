from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from utils.mixin import LoginRequiredMixin

from datetime import datetime

# Create your views here.

# /order/place


class OrderPlaceView(LoginRequiredMixin, View):
    '''订单页面显示'''

    def post(self, request):
        '''订单页面显示'''

        # 获取用户
        user = request.user

        # 获取购买的商品id
        sku_ids = request.POST.getlist('sku_id')

        # 校验参数,无商品则跳转到主页面
        if not sku_ids:
            return redirect(reverse('cart:show'))

        # 获取购买的商品,计算小计、总价、
        skus = []
        total_price = 0  # 总金额
        total_count = 0  # 商品总数量
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)

            # 查询购物车：商品数量
            conn = get_redis_connection('default')
            cart_key = f'cart_{user.id}'
            count = conn.hget(cart_key, sku_id)

            # 计算小计
            amount = sku.price * int(count)
            sku.amount = amount
            sku.count = count
            skus.append(sku)

            # 总计
            total_price += amount
            total_count += int(count)

        # 运费与实款
        transit_price = 10
        total_pay = total_price + transit_price

        # 获取用户地址
        addresses = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)

        # 组织上下文
        context = {'skus': skus,
                   'sku_ids': sku_ids,
                   'addrs': addresses,
                   'total_price': total_price,
                   'total_count': total_count,
                   'transit_price': transit_price,
                   'total_pay': total_pay}

        # 返回
        return render(request, 'place_order.html', context)

# /order/commit
class OrderCommitView(View):
    '''订单提交处理'''

    def post(self, request):
        '''订单提交'''

        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户没有登录'})

        # 获取订单信息
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_id = request.POST.get('pay_id')

        # 数据完整性判断
        if not all([sku_ids, addr_id, pay_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_id not in OrderInfo.PAY_METHODS:
            return JsonResponse({'res': 2, 'errmsg': '不支持的支付方式'})

        # 校验收货地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '收货地址不存在'})

        # todo:创建订单核心业务
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)  # 订单id
        total_price = 0  # 订单总价格
        total_count = 0  # 订单商品总数
        transit_price = 10  # 运费

        # todo:向df_order_info表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                 user=user,
                                 addr=addr,
                                 pay_method=pay_id,
                                 total_price=total_price,
                                 total_count=total_count,
                                 transit_price=transit_price,)

        # 连接redis
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'

        sku_ids = sku_ids.split(',')
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

            count = conn.hget(cart_key, sku_id)

            # todo:向df_order_good表中添加多条商品记录
            order_goods = OrderGoods.objects.create(order = order,
                                      sku = sku,
                                      count = count,
                                      price = sku.price,)

            # todo:更新库存和销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 计数订单商品总数和总价
            total_count += int(count)
            total_price += sku.price * int(count)

        # 更新订单
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # 删除购物车记录
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})
