from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.views.generic import View
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from order.models import OrderGoods
from django_redis import get_redis_connection


# Create your views here.

# http://192.168.18.129:8000/index
class IndexView(View):

    def get(self, request):
        '''网站首页'''

        context = cache.get('index_page_data')

        if context is None:
            print('设置缓存')
            # 获取商品的种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types:
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(
                    type=type, display_type=1).order_by('index')

                # 获取type种类首页分离额商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(
                    type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            cache.set('index_page_data', context, 3600)

        # 从redis中获取购物车信息
        user = request.user
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_count = conn.hlen(f'cart_{user.id}')

        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


# /detail/id
class DetailView(View):
    '''详情页面'''

    def get(self, request, goods_id):
        '''显示详情页'''

        # 获取商品种类
        types = GoodsType.objects.all()

        # 获取该商品id的对象
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except sku.DoseNotExists:
            return redirect(reverse('goods:index'))

        # 获取商品评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品
        new_skus = GoodsSKU.objects.filter(
            type=sku.type).order_by('-create_time')

        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 获取购物车商品数量
            conn = get_redis_connection('default')
            cart_count = conn.hlen(f'cart_{user.id}')

            # 添加历史浏览记录
            conn = get_redis_connection('default')
            history_key = f'history_{user.id}'
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        context = {'sku': sku,
                   'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'cart_count': cart_count}

        # 使用模板,返回页面
        return render(request, 'detail.html', context)
