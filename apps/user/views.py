from django.shortcuts import render, redirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.conf import settings
from django_redis import get_redis_connection
from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re

# Create your views here.

# /user/register
class RegisterView(View):
    '''注册'''

    def get(self, request):
        # 显示注册页面
        return render(request, 'register.html')

    def post(self, request):
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all((username, password, email)):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(
            r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',
                email):
            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})

        # 同意协议校验
        if not allow:
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 注册用户
        user = User.objects.create_user(username, email, password)
        user.is_active = False
        user.save()

        # 发激活邮件
        # 加密用户身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf8')

        # 发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答, 跳转到首页
        return redirect(reverse('goods:index'))

# user/active/用户id


class ActiveView(View):
    '''激活用户'''

    def get(self, request, token):
        # 进行用户激活
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')


# user/login
class LoginView(View):
    '''登录'''

    def get(self, request):
        # 显示登录页面

        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(
            request, 'login.html', {
                'username': username, 'checked': checked})

    def post(self, request):
        # 登录校验

        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)

                next_url = request.GET.get('next', reverse('goods:index'))

                response = redirect(next_url)
                remember = request.POST.get('remember')
                if remember:
                    response.set_cookie(
                        'username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

# /user/logout


class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))

# /user


class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''

    def get(self, request):
        address = Address.objects.get_default_address(user=request.user)

        # 获取历史浏览记录
        # 连接redis
        con = get_redis_connection('default')

        # 查找redis, 获取用户历史浏览商品id列表
        sku_ids = con.lrange(f'history_{request.user.id}', 0, 4)

        # 按浏览记录顺序获取商品
        goods_list = []
        for id in sku_ids:
            try:
                goods = GoodsSKU.objects.get(id=id)
            except GoodsSKU.DoesNotExist:
                pass

            goods_list.append(goods)

        context = {'page': 'info', 'address': address, 'goods_list': goods_list}
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''

    def get(self, request, page):
        '''订单显示页'''

        #  获取用户
        user = request.user

        # 获取用户的订单信息, 遍历所有订单
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 获取当前用户订单商品
        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order)

            for order_sku in order_skus:
                # 商品小计
                amount = order_sku.price * int(order_sku.count)
                order_sku.amount = amount # 订单商品动态增加属性

            order.order_skus = order_skus # 订单动态增加属性

            # 动态增加订单状态字符串
            status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.status_name = status_name


        # 订单信息分页
        paginator = Paginator(orders, 1)

        # 获取当前页
        page = int(page)
        order_page = paginator.page(page)

        # 控制页码显示
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 组织上下文
        context = {'page': 'order',
                   'order_page': order_page,
                   'pages': pages,}

        # 使用模板
        return render(request, 'user_center_order.html', context)

# /user/address
class UserAddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''

    def get(self, request):
        # 获取登录用户的默认收货地址
        address = Address.objects.get_default_address(user=request.user)
        context = {'page': 'address', 'address': address}
        return render(request, 'user_center_site.html', context)

    def post(self, request):

        # 获取收货地址
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据完整性
        if not all([receiver, addr, phone]):
            return render(
                request, 'user_center_site.html', {
                    'errmsg': '数据不完整'})

        # 校验手机号码
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}', phone):
            return render(
                request, 'user_center_site.html', {
                    'errmsg': '手机号码不正确'})

        # 业务处理: 地址添加
        address = Address.objects.get_default_address(user=request.user)
        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(
            user=request.user,
            receiver=receiver,
            addr=addr,
            zip_code=zip_code,
            phone=phone,
            is_default=is_default)


        # 重定位页面
        return redirect(reverse('user:address'))
