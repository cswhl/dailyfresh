from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.core.paginator import Paginator
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
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品
        new_skus = GoodsSKU.objects.filter(
            type=sku.type).order_by('-create_time')

        # 获取同一个SPU的其它规格商品
        same_spu_skus = GoodsSKU.objects.filter(
            goods=sku.goods).exclude(id=goods_id)

        # 获取购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_count = conn.hlen(f'cart_{user.id}')

            # 添加历史浏览记录
            conn = get_redis_connection('default')
            history_key = f'history_{user.id}'
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        context = {'sku': sku,
                   'same_spu_skus': same_spu_skus,
                   'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'cart_count': cart_count}

        # 使用模板,返回页面
        return render(request, 'detail.html', context)

# /list/种类id/页码?sort=排列方式


class ListView(View):
    '''商品列表'''

    def get(self, request, type_id, page):
        '''显示列表页'''

        # 获取该商品种类
        type = None
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()

        # 根据默认、价格、销量显示该类的所有商品
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 5)

        # 获取商品页的内容
        try:
            page = int(page)
        except TypeError:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page对象
        skus_page = paginator.page(page)

    # todo: 进行页码的控制，页面上最多显示5个页码
    # 1.总页数小于5页，页面上显示所有页码
    # 2.如果当前页是前3页，显示1-5页
    # 3.如果当前页是后3页，显示后5页
    # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取该类商品的新品
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-update_time')[:5]

        # 获取购物车
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_count = conn.hlen(f'cart_{user.id}')

        #
        context = {'type': type,
                   'types': types,
                   'skus_page': skus_page,
                   'new_skus': new_skus,
                   'sort': sort,
                   'cart_count': cart_count,
                   'pages': pages}

        # 渲染模板，返回
        return render(request, 'list.html', context)
