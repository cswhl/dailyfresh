from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.db import transaction
from django_redis import get_redis_connection
from alipay import AliPay

from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from utils.mixin import LoginRequiredMixin

from datetime import datetime
import os

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
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('cart:show'))


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

    @transaction.atomic
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

        save_id = transaction.savepoint() # 创建保存点
        try:
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
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id) # 悲观锁
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                count = conn.hget(cart_key, sku_id)

                # print(f'用户={user.id}', f'库存={sku.stock}')
                # import time
                # time.sleep(10)

                # 判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 5, 'errmsg': '商品库存不足'})


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
        except Exception as e:
            print(e)
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 6, 'errmsg': '订单创建失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # 删除购物车记录
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 7, 'errmsg': '订单创建成功'})

# /order/pay
class OrderPayView(View):
    '''支付'''

    def post(self, request):
        '''支付'''

        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})


        # 获取订单id
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效订单'})

        print(order_id)
        print(user)
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user = user,
                                          pay_method = 3,
                                          order_status = 1,
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 调用支付宝API
        # 初始化支付对象
        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102400749214", # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False，使用沙箱环境时置为True
        )

        # 调用支付API
        total_pay = order.total_price+order.transit_price # Decimal 是不能序列化的，应转换字符串
        # 电脑网站支付
        try:
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=order_id, # 订单id
                total_amount=str(total_pay), # 支付总金额
                subject='天天生鲜%s' % order_id,
                return_url="https://example.com",
                notify_url="https://example.com/notify" # 可选, 不填则使用默认notify url
            )
        except Exception as e:
            print(e)

        # 返回：提交支付页面url
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':3, 'pay_url':pay_url}) # 将支付地址回传给浏览器，从而引导用户跳转到支付页面

# /order/check
class OrderCheckView(View):
    '''查询支付结果'''

    def post(self, request):
        '''查询支付结果'''

        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})


        # 获取订单id
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效订单'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user = user,
                                          pay_method = 3,
                                          order_status = 1,
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 初始化支付对象
        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102400749214", # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False，使用沙箱环境时置为True
        )

        # 调用查询支付结果API,其中response是保存结果的字典，详见API的说明
        response = alipay.api_alipay_trade_query(out_trade_no=order_id)

        code = response.get('code')
        while True:
            if code == "10000" and response['trade_status'] == "TRADE_SUCCESS": # 订单支付成
                # 更新支付编号和订单状态
                order.trade_no = response.get('trade_no')
                order.order_status = 4
                order.save()
                return JsonResponse({'res': 3, 'errmsg': '订单支付成功'})
            elif code == "40004" or (code == "10000" and response['trade_status'] == "WAIT_BUYER_PAY"): # 订单待支付
                import time
                time.sleep(5)
                continue
            else:
                return JsonResponse({'res': 4, 'errmsg': '订单支付失败'})
