from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from goods.models import GoodsSKU
from django_redis import get_redis_connection

# Create your views here.

# /cart/add


class CartAddView(View):
    '''购物车记录添加'''

    def post(self, request):
        '''添加商品到购车'''

        # 1.判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({{'res': 0, 'errmsg': '用户没有登录'}})

        # 2.获取商品id和数量
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 3.判断数据是否完整
        if not all([sku_id, count]):
            return JsonResponse({{'res': 1, 'errmsg': '数据不完整'}})

        # 4.检验添加的商品数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({{'res': 2, 'errmsg': '商品数目出错'}})

        # 4.查询数据库:该商品id是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({{'res': 3, 'errmsg': '商品不存在'}})

        # 5.业务处理:添加购物车记录
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            # 累加购物车商品的数目
            count += int(cart_count)

        # 6.校验商品的库存
        if count > sku.stock:
            return JsonResponse({{'res': 4, 'errmsg': '库存不足'}})

        conn.hset(cart_key, sku_id, count)  # 设置hash中sku_id对应的值

        # 返回应答
        return JsonResponse({{'res': 5, 'errmsg': '添加成功'}})
