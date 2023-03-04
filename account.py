import http
import json

from collections import OrderedDict

import requests

import chatgpt
from statistics import RequestCounter


class Account:
    def __init__(self, id_: str, email: str, session_token: str, proxy: str = None):
        self.id = id_
        self.email = email
        self.session_token = session_token
        self.session_info: chatgpt.SessionInfo = None
        self.is_logged_in: bool = False
        self.session: requests.Session = requests.Session()
        self.is_busy = False
        self.counter = RequestCounter(3600)
        self.err_msg = ""
        if proxy is not None:
            self.session.proxies.update({
                "http": proxy,
                "https": proxy,
            })
        self.proxy = proxy

    def login(self) -> bool:
        try:
            self.session_info = chatgpt.login_with_cookie(self.session_token, self.proxy)
        except requests.HTTPError as err:
            self.err_msg = str(err)
            return False
        chatgpt.set_session(self.session, self.session_info.access_token)
        self.is_logged_in = self.logged_in()
        return self.is_logged_in

    def load_session(self, session_json_file: str):
        with open(session_json_file, 'rb') as f:
            session_json = json.loads(f.read())
        self.session_info = chatgpt.SessionInfo(session_json)

    def save_session(self, session_json_file: str):
        with open(session_json_file, 'w') as f:
            f.write(json.dumps(self.session_info.__dict__(), indent=2))

    def login_with_session_info(self) -> bool:
        if self.session_info is None:
            self.err_msg = "no session info"
            return False
        chatgpt.set_session(self.session, self.session_info.access_token)
        self.is_logged_in = self.logged_in()
        return self.is_logged_in

    def logged_in(self) -> bool:
        if self.session_info is None:
            self.err_msg = "no session info"
            return False
        if self.session_info.user is None:
            self.err_msg = "no user info"
            return False
        if self.session_info.user.email != self.email:
            self.err_msg = f"email not match: {self.session_info.user.email}"
            return False
        response = chatgpt.get_models(self.session)
        if response.status_code == http.HTTPStatus.OK:
            models = json.loads(response.content)
            r = chatgpt.get_response_body_detail(models)
            if r is not None:
                self.err_msg = r[0]
                return False
            models_obj = models.get("models")
            if models_obj is None:
                self.err_msg = "no modules"
                return False
            for model in models_obj:
                if model["slug"] == chatgpt.CHATGPT_DEFAULT_MODEL:
                    self.err_msg = ""
                    return True
            self.err_msg = "no slug module"
            return False
        self.err_msg = response.content.decode()
        return False

    @staticmethod
    def from_dict(account_config: dict, proxy: str = None):
        id_ = account_config["id"]
        email = account_config["email"]
        session_token = account_config["session_token"]
        return Account(id_, email, session_token, proxy)

    def __dict__(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "session_token": self.session_token,
        }


class Accounts:
    def __init__(self):
        self.accounts: OrderedDict[str, Account] = OrderedDict()
        self.proxy: str = None

    def load(self, config: dict):
        assert type(config.get("accounts")) == list
        self.proxy = config.get("proxy")
        for account_config in config["accounts"]:
            account = Account.from_dict(account_config, self.proxy)
            self.accounts[account.id] = account

    def save(self, config_file: str):
        accounts_list = []
        for id_ in self.accounts:
            accounts_list.append(self.accounts[id_].__dict__())
        with open(config_file, "w") as f:
            f.write(json.dumps({
                "proxy": self.proxy,
                "accounts": accounts_list,
            }, indent=2))

    def set(self, account: Account):
        self.accounts[account.id] = account
