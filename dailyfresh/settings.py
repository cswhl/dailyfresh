"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*+81kwzvevd7vpw$3&19dgr3qec^(0p#l7glv$p4t5mf!=se4h'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []

# DEBUG = False
# ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'haystack', # 全文搜索框架
    'tinymce', # 富文本编辑器
    'user',
    'goods',
    'cart',
    'order',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates').replace('\\', '/')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',  # 数据库名字，数据库必须手动创建
        'USER': 'cs1',  # 连接mysql的用户名
        'PASSWORD': '1234',  # 用户对的密码
        'HOST': '192.168.18.129',  # 指定mysql数据库所在的电脑ip
        'PORT': 3306,  # mysql服务的端口号
        'OPTIONS': {"init_command":"SET foreign_key_checks=0"},
    }
}

# django认证系统使用的模型类
AUTH_USER_MODEL = 'user.User'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'), ]

# 富文本编辑器配置
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'width': 600,
    'height': 400,
}

# 发送邮件配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# smpt服务地址
EMAIL_HOST = 'smtp.126.com'
EMAIL_PORT = 25
# 发送邮件的邮箱
EMAIL_HOST_USER = 'cswhltime@126.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'PDSWHUPTVTAGGSLP'
# 收件人看到的发件人,邮箱地址必须和上面一样，否者发不出去?
EMAIL_FROM = '天天生鲜<cswhltime@126.com>'


# django的缓存配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache", # 使用redis作为缓存
        "LOCATION": "redis://192.168.18.129:6379/9",
        "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# 配置session存储,将session保存到缓存中:在已经使用redis作为缓存后，session会直接存储在redis缓存
SESSION_ENGINE = "django.contrib.sessions.backends.cache" # 默认本机内存作为缓存，设置redis后,redis作为缓存后
SESSION_CACHE_ALIAS = "default"

# 配置默认登录地址
LOGIN_URL = '/user/login'

# 配置django的文件存储类
DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FDFSStorage'

FDFS_CLIENT_CONF = './utils/fdfs/client.conf'
FDFS_URL = 'http://192.168.18.129:8888/'

# 配置搜索引擎
HAYSTACK_CONNECTIONS = {
    'default': {
                'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine', # 使用whoosh搜索引擎
                'PATH': os.path.join(BASE_DIR, 'whoosh_index'), # 索引文件路径
    },
}

# 当添加、修改、删除数据时,自定生成索引
HATSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
