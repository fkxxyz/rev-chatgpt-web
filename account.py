import http
import json

from collections import OrderedDict

import requests

import chatgpt


class Account:
    def __init__(self, id_: str, email: str, session_token: str, proxy: str = None):
        self.id = id_
        self.email = email
        self.session_token = session_token
        self.access_token: str = ""
        self.session: requests.Session = requests.Session()
        if proxy is not None:
            self.session.proxies.update({
                "http": proxy,
                "https": proxy,
            })
        self.proxy = proxy

    def login(self):
        access_token = chatgpt.login_with_cookie(self.session_token, self.proxy)
        chatgpt.set_session(self.session, access_token)
        logged_in = self.logged_in()
        assert logged_in
        self.access_token = access_token

    def login_with_token(self, access_token: str):
        chatgpt.set_session(self.session, access_token)
        logged_in = self.logged_in()
        if logged_in:
            self.access_token = access_token
            return
        else:
            self.login()

    def logged_in(self) -> bool:
        if len(self.session_token) == 0:
            return False
        response = chatgpt.get_models(self.session)
        if response.status_code == http.HTTPStatus.OK:
            models = json.loads(response.content)
            for model in models.get("models"):
                if model["slug"] == chatgpt.CHATGPT_DEFAULT_MODEL:
                    return True
            return False
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

    def load(self, config: dict):
        assert type(config.get("accounts")) == list
        for account_config in config["accounts"]:
            account = Account.from_dict(account_config, config.get("proxy"))
            self.accounts[account.id] = account

    def save(self, config_file: str):
        accounts_list = []
        for id_ in self.accounts:
            accounts_list.append(self.accounts[id_].__dict__())
        with open(config_file, "w") as f:
            f.write(json.dumps(accounts_list))

    def set(self, account: Account):
        self.accounts[account.id] = account
