# 使用celery
from django.core.mail import send_mail
from django.template import loader
from django.conf import settings
from celery import Celery
import os

# 在任务处理者一端加：django环境的初始化
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daillyfresh.settings")
# django.setup()

from goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner

# 创建一个Celery类的实例对象，celery_tasks.tasks是创建worker显示的app名，可以随意指定，但推荐使用“包名.模块名”(容易分辨)
app = Celery('celery_tasks.tasks', broker='redis://192.168.18.129:6379/8')

# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '<h1>%s,欢迎你成为天天生鲜注册会员</h1>请点击下面链接激活你的账户<br/>' \
                   '<a href="http://192.168.18.129:8000/user/active/%s">http://192.168.18.129:8000/user/active/%s</a>' %(username, token, token)
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    send_mail(subject, message, sender, receiver, html_message=html_message)


@app.task
def generate_static_index_html():
    '''产生首页静态页面'''

    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销搞活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')

        # 获取type种类首页分离额商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners,}
    # 使用模板
    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(context)

    # 生成首页html内容
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
