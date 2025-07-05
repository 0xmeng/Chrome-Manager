import atexit
import os
import sys
import time
from typing import Dict, Any
import yaml
import requests
from pathlib import Path
import subprocess

# Clash API URL
CLASH_API_URL = "http://127.0.0.1"  # Replace with your Clash API address if different
SECRET = ""  # Set this if you configured a secret in config.yaml
# 获取当前用户主目录
home_dir = os.path.expanduser("~")
# 拼接 .config 路径
CONFIG_PATH = os.path.join(home_dir, ".config\clash\profiles")

MIXED_PORT_START=50000
PORT_GAP=10


def read_config(config_path) -> Dict[str, Any]:
    """读取YAML配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return {}


class ClashAPI:

    proxy_files={}

    def __init__(self, index=0):
        self.index = index
        self.config_exists = False
        self.port = MIXED_PORT_START + index + index * PORT_GAP
        self.api_proxy = f"{CLASH_API_URL}:{self.port}"
        self.proxy = f"{CLASH_API_URL}:{self.port+2}"
        print(f"proxy: {self.proxy}")
        # ClashAPI.load_configs()
        self.start_clash()
        self.server = None

    @classmethod
    def is_clash_config_exists(clz):
        if clz.proxy_files:
            return True
        return False

    def start_clash(self):
        if not self.proxy_files:
            print("clash配置文件未加载")
            return
        # 当前文件目录的上一级目录

        if getattr(sys, 'frozen', False):
            # ✅ 打包后的 .exe 路径
            parent_dir = Path(sys.executable).parent
        else:
            # ✅ 脚本运行时的路径
            parent_dir = Path(__file__).resolve().parent

        # 构造目标文件路径
        config_path = parent_dir / "clash" / "config.yaml"
        dict = read_config(config_path)
        print(dict)

        """创建临时配置文件"""

        new_config_path = parent_dir / "clash" / f"{self.index}.yaml"
        if os.path.exists(new_config_path):
            print(f"modify config exists {self.index}.yaml")
        else:
            temp_config = dict.copy()
            temp_config["mixed-port"] = self.port
            temp_config["redir-port"] = self.port + 1
            temp_config["external-controller"] = f"127.0.0.1:{self.port + 2}"
            # 写入配置
            with open(new_config_path, 'w', encoding='utf-8') as file:
                yaml.dump(temp_config, file, allow_unicode=True)

        clash_path = parent_dir / "clash/x64/clash-win64.exe"
        self.start_clash_server(new_config_path, clash_path)
        return new_config_path

    def close_server(self):
        if self.server:
            self.server.terminate()
            print(f">>>> 关闭clash 服务 {self.index}")

    def start_clash_server(self, config_path: str, clash_path: str = "clash") -> None:
        """启动Clash进程"""

        try:
            # 使用subprocess启动clash
            proc = subprocess.Popen([clash_path, "-f", config_path],
                                    stdout=subprocess.DEVNULL,   # 等价于 > /dev/null
                                    stderr=subprocess.DEVNULL,   # 等价于 2>&1
                                    stdin=subprocess.DEVNULL,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"Clash已启动，使用配置文件: {config_path}")
            self.server = proc

            # 程序退出时自动终止子进程
            atexit.register(proc.terminate)
            time.sleep(2)
        except Exception as e:
            print(f"启动Clash失败 {self.index}: {e}")

    @classmethod
    def get_proxy_for_table(cls):
        if not cls.proxy_files:
            return
        group_names = []
        proxies_in_groups = {}
        for key, value in cls.proxy_files.items():
            print(f"{key} => {value}")
            group_names.append(key)
            proxies = value.get("proxies")
            if proxies:
                proxies_in_groups[key] = value.get("proxies")

        return group_names, proxies_in_groups

    @classmethod
    def load_configs(cls):

        if os.path.exists(CONFIG_PATH):
            print("目录存在")
            # 你要搜索的目录（可以是绝对路径或相对路径）
            directory = Path(CONFIG_PATH)

            yaml_files = list(directory.rglob("*.yml")) + list(directory.rglob("*.yaml"))

            # 输出文件列表
            for file in yaml_files:
                # print(file)
                dict = read_config(file)
                if dict:
                    proxy_groups = dict.get("proxy-groups")
                    if proxy_groups:
                        if isinstance(proxy_groups, list) and len(proxy_groups) > 0:
                            first_group = proxy_groups[0]
                            if first_group and first_group.get("name"):
                                proxy_name = first_group.get("name")
                                proxies = first_group.get("proxies")
                                if proxy_name and proxies:
                                    cls.proxy_files[proxy_name] = {"file_path": file.as_posix(), "proxies": proxies}

            # print(cls.proxy_files)
            return cls.proxy_files

        else:
            print("目录不存在")



    # Function to switch proxy
    def switch_proxy(self, group_name, proxy_name):
        url = f"{self.proxy}/proxies/{group_name}"
        headers = {}

        if SECRET:
            headers["Authorization"] = f"Bearer {SECRET}"

        # Data to switch the proxy
        data = {"name": proxy_name, "group": group_name}

        response = requests.put(url, json=data, headers=headers)
        if response.status_code == 204:
            print(f"成功切换到代理: {proxy_name} 组: {group_name}")
            return True
        else:
            print(
                f"切换代理失败.  {proxy_name} 组: {group_name} Status: {response.status_code}, Response: {response.text}")

        # Function to list proxies in a group

    def list_proxies(self, group_name):
        url = f"{self.proxy}/proxies/{group_name}"
        headers = {}

        if SECRET:
            headers["Authorization"] = f"Bearer {SECRET}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            proxies = response.json().get("all", [])
            print(f"Proxies in group '{group_name}': {proxies}")
            return proxies
        else:
            print(f"Failed to fetch proxies. Status: {response.status_code}, Response: {response.text}")
            return []

    def get_configs(self):
        print('')
        url = f"{self.proxy}/configs"
        headers = {}

        if SECRET:
            headers["Authorization"] = f"Bearer {SECRET}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response)
            proxies = response.json().get("all", [])
            # print(f"Proxies in group '{group_name}': {proxies}")
            return proxies
        else:
            print(f"Failed to fetch proxies. Status: {response.status_code}, Response: {response.text}")
            return []

    def switch_config_proxy(self, group_name):
        url = f"{self.proxy}/configs/"
        print(url)
        headers = {}

        if SECRET:
            headers["Authorization"] = f"Bearer {SECRET}"
        print("---->>> self.proxy_files")
        # print(self.proxy_files)
        profile = self.proxy_files.get(group_name)
        if not profile:
            print(f"配置文件加载失败 {group_name}")
            return False
            # profile = "速鹰666"

        path = profile.get("file_path")
        if not path:
            print(f"找不到配置文件 {group_name}")
            return False
        # Data to switch the proxy
        data = {"path": f"{path}"}

        response = requests.put(url, json=data, headers=headers)
        if response.status_code == 204:
            print(f"成功切换到组: {group_name}")
            return True
        else:
            print(f"切换 组: {group_name} Status: {response.status_code}, Response: {response.text}")

    def switch_clash_proxy(self, group_name, proxy_name):
        ip_name = str(proxy_name).strip()
        success = False
        retry = 0
        while not success and retry < 5:
            success = self.switch_config_proxy(group_name)
            success = self.switch_proxy(group_name, ip_name)
            if success:
                return success
            time.sleep(2)
            tmp_ip_Name = ip_name.strip()
            ip_name = f"{tmp_ip_Name} "
            retry += 1
            print(f">>>> 代理切换失败，重试{retry}")
        return success


# Example usage
if __name__ == "__main__":
    group_name = "泡泡Dog"
    proxy = "日本01"
    c = ClashAPI(1)

    c.start_clash()
    time.sleep(10)
    # clash切换到 青云代理 配置文件
    c.switch_config_proxy(group_name)
    # 打印所有dialing线路
    # c.list_proxies()
    # 切换到 日本01 线路
    c.switch_proxy(group_name, proxy)
    input("按 Enter 键退出程序...")