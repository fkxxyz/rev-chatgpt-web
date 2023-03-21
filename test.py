import json
import os

from account import Account

home_path = os.getenv("HOME")
config = json.load(open(os.path.join(home_path, ".config", "revChatGPT", "config.json")))
cache = json.load(open(os.path.join(home_path, ".cache", "revChatGPT", "config.json")))

# 从配置读取 token
session_token = config['accounts'][0]['session_token']
access_token = cache['access_token']

account = Account("fkxxyz", "fkxxyz@xxxx.com", "xxxxxxxx", session_token, "/tmp", config['proxy'])

# 尝试用 access_token 访问
is_logged_in = account.login_with_session_info()

# 用 session_token 登录得到 access_token
if not is_logged_in:
    is_logged_in = account.login()
