from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    '''fastdfs文件存储类'''

    def __init__(self, client_conf=None, base_url=None):
        '''初始化'''

        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        '''打开文件'''
        pass

    def _save(self, name, content):
        '''存储文件'''

        # 创建客户端
        client = Fdfs_client(self.client_conf)

        # 上传问题到fastdfs
        res = client.upload_by_buffer(content.read())
        # res对象的格式
        # dict {
        #     'Group name'      : group_name,
        #     'Remote file_id'  : remote_file_id,
        #     'Status'          : 'Upload successed.',
        #     'Local file name' : '',
        #     'Uploaded size'   : upload_size,
        #     'Storage IP'      : storage_ip
        # }

        # 判断文件是否上传成功
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到fastdfs失败')

        # 获取文件id
        filename = res.get('Remote file_id')

        # 返回真实文件名,会被存储到mysql数据库
        return filename

    def exists(self, name):
        '''Django判断文件名是否可用？'''
        return False

    def url(self, name):
        '''返回访问文件的url路径'''

        return self.base_url + name
