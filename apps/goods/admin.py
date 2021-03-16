from django.contrib import admin
from django.core.cache import cache
from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from goods.models import Goods, GoodsSKU

# Register your models here.


@admin.register(GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner,IndexPromotionBanner)
class BaseModelAdmin(admin.ModelAdmin):
    '''自定义模型管理类'''

    def save_model(self, request, obj, form, change):
        '''新增或更新表中数据时被调用'''
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        '''删除表中数据时被调用'''
        super().delete_model(request, obj)

        # 发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')


admin.site.register(Goods)
admin.site.register(GoodsSKU)
