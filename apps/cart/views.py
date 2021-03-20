from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection

# Create your views here.

# 类视图不能继承LoginRequiredMixin,因为AXJX请求都在后台运行，在浏览器中不能看到效果(即不会跳显示登录页面)
# /cart/add


class CartAddView(View):
    '''购物车记录添加'''

    def post(self, request):
        '''添加商品到购车'''

        # 1.判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            print(user)
            return JsonResponse({'res': 0, 'errmsg': '用户没有登录'})

        # 2.获取商品id和数量
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 3.判断数据是否完整
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 4.检验添加的商品数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 4.查询数据库:该商品id是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 5.业务处理:添加购物车记录
        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            # 累加购物车商品的数目
            count += int(cart_count)

        # 6.校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存不足'})

        conn.hset(cart_key, sku_id, count)  # 设置hash中sku_id对应的值

        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count,
                             'errmsg': '添加成功'})

# /cart/


class CartInfoView(LoginRequiredMixin, View):
    '''购物车'''

    def get(self, request):
        '''购物车页面显示'''

        # 获取用户购物中商品的信息
        user = request.user
        cart_key = f'cart_{user.id}'
        conn = get_redis_connection('default')
        skus = []
        total_count = 0
        total_price = 0
        for sku_id, count in conn.hgetall(cart_key).items():
            # 遍历:使用商品id获取所有商品,并动态绑定商品数量属性
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品小计
            amount = sku.price * int(count)
            sku.amount = amount
            sku.count = count
            skus.append(sku)

            # 累积商品总数和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price}

        # 返回
        return render(request, 'cart.html', context)
