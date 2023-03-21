import http
import json
import os.path

from collections import OrderedDict

import requests

import OpenAIAuth
import chatgpt
from statistics import RequestCounter


class Account:
    def __init__(self, id_: str, email: str, password: str, session_token: str, cache_path: str,
                 disabled: bool = False, proxy: str = None):
        self.id = id_
        self.email = email
        self.password = password
        self.session_token = session_token
        self.session_info: chatgpt.SessionInfo | None = None
        self.is_logged_in: bool = False
        self.session: requests.Session = requests.Session()
        self.is_disabled = disabled
        self.is_busy = False
        self.counter = RequestCounter(7200, os.path.join(cache_path, self.id + ".counter.json"))
        self.err_msg = ""
        if proxy is not None:
            self.session.proxies.update({
                "http": proxy,
                "https": proxy,
            })
        self.proxy = proxy

    def login_with_password(self) -> bool:
        print(f"password login({self.email}) ...")
        try:
            self.session_token = chatgpt.login(self.email, self.password, self.proxy)
            print(f"password login({self.email}) success")
            return True
        except (requests.RequestException, OpenAIAuth.Error) as err:
            self.err_msg = str(err)
            print(f"password login({self.email}) failed")
            return False

    def login(self) -> bool:
        print(f"session_token login({self.email}) ...")
        try:
            self.session_info = chatgpt.get_session_info(self.session_token, self.proxy)
        except requests.RequestException as err:
            self.err_msg = str(err)
            return False
        chatgpt.set_session(self.session, self.session_info.access_token)
        self.is_logged_in = self.logged_in()
        if self.is_logged_in:
            print(f"session_token login({self.email}) success")
        else:
            print(f"session_token login({self.email}) failed")
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
        print(f"access_token login({self.email}) ...")
        chatgpt.set_session(self.session, self.session_info.access_token)
        self.is_logged_in = self.logged_in()
        if self.is_logged_in:
            print(f"access_token login({self.email}) success")
        else:
            print(f"access_token login({self.email}) failed")
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
        try:
            response = chatgpt.get_models(self.session, 10)
        except requests.RequestException as err:
            self.err_msg = str(err)
            return False
        if response.status_code == http.HTTPStatus.OK:
            try:
                models = json.loads(response.content)
            except json.JSONDecodeError:
                self.err_msg = response.content.decode()
                return False
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
        self.err_msg = f"http status({response.status_code}): " + response.content.decode()
        return False

    @staticmethod
    def from_dict(account_config: dict, cache_path: str, proxy: str | None = None):
        id_ = account_config["id"]
        email = account_config["email"]
        password = account_config.get("password")
        if password is None:
            password = ""
        session_token = account_config["session_token"]
        disabled = account_config.get("disabled") or False
        return Account(id_, email, password, session_token, cache_path, disabled, proxy)

    @staticmethod
    def from_session_info(id_: str, password: str, session_token: str, session_info: chatgpt.SessionInfo,
                          cache_path: str, proxy: str | None = None):
        account = Account(id_, session_info.user.email, password, session_token, cache_path, False, proxy)
        account.session_info = session_info
        print(f"session_token login({account.email}) ...")
        chatgpt.set_session(account.session, account.session_info.access_token)
        account.is_logged_in = account.logged_in()
        if account.is_logged_in:
            print(f"session_token login({account.email}) success")
        else:
            print(f"session_token login({account.email}) failed")
        return account

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "password": self.password,
            "session_token": self.session_token,
            "disabled": self.is_disabled,
        }


class Accounts:
    def __init__(self, cache_path: str):
        self.accounts: OrderedDict[str, Account] = OrderedDict()
        self.__cache_path = cache_path
        self.proxy: str | None = None

    def load(self, config: dict):
        assert type(config.get("accounts")) == list
        self.proxy = config.get("proxy")
        for account_config in config["accounts"]:
            account = Account.from_dict(account_config, self.__cache_path, self.proxy)
            self.accounts[account.id] = account

    def save(self, config_file: str):
        accounts_list = []
        for id_ in self.accounts:
            accounts_list.append(self.accounts[id_].asdict())
        with open(config_file, "w") as f:
            f.write(json.dumps({
                "proxy": self.proxy,
                "accounts": accounts_list,
            }, indent=2))

    def apply(self, email: str, password: str, session_token: str, config_file: str) -> Account:
        if len(session_token) == 0:
            if len(email) == 0 or len(password) == 0:
                raise requests.RequestException("no email or password")
            try:
                print(f"password login({email}) ...")
                session_token = chatgpt.login(email, password, self.proxy)
                print(f"password login({email}) success")
            except (requests.RequestException, OpenAIAuth.Error) as err:
                print(f"password login({email}) failed")
                raise err
        try:
            session_info = chatgpt.get_session_info(session_token, self.proxy)
        except requests.RequestException as err:
            raise err
        for id_ in self.accounts:
            if self.accounts[id_].email == session_info.user.email:
                account = self.accounts[id_]
                account.session_info = session_info
                print(f"session_token login({account.email}) ...")
                chatgpt.set_session(account.session, account.session_info.access_token)
                account.is_logged_in = account.logged_in()
                if account.is_logged_in:
                    print(f"session_token login({account.email}) success")
                else:
                    print(f"session_token login({account.email}) failed")
                break
        else:
            account = Account.from_session_info(
                session_info.user.email, password, session_token, session_info,
                self.__cache_path, self.proxy,
            )
            self.accounts[session_info.user.email] = account
        self.save(config_file)
        account.save_session(os.path.join(self.__cache_path, self.__cache_path, account.id + ".json"))
        return account

    def set(self, account: Account):
        self.accounts[account.id] = account
