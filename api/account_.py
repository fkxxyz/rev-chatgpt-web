import http
import os

import flask
import requests

import OpenAIAuth
from account import Account
from api import app
from api.common import globalObject


def get_account_query(account_id: str, must_logged_in: bool = True) -> (Account, flask.Response):
    account: Account = globalObject.default_account
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.accounts.get(account_id)
    if account is None:
        return None, flask.make_response('error: no such account', http.HTTPStatus.FORBIDDEN)
    if must_logged_in and not account.is_logged_in:
        return account, flask.make_response('error: account is not logged in', http.HTTPStatus.UNAUTHORIZED)
    return account, None


def account_login_with_access_token(account: Account):
    if account.session_info is not None:
        if len(account.session_info.access_token) != 0:
            account.login_with_session_info()
    if account.is_logged_in:
        account.save_session(os.path.join(globalObject.cache_path, account.id + ".json"))


def account_login_with_session_token(account: Account):
    account.login()
    if account.is_logged_in:
        account.save_session(os.path.join(globalObject.cache_path, account.id + ".json"))


def account_login_with_password(account: Account):
    account.login_with_password()
    if account.is_logged_in:
        account.save_session(os.path.join(globalObject.cache_path, account.id + ".json"))
        globalObject.accounts.save(globalObject.config_path)


# 标记帐号 token 已无效
def account_logout(account: Account):
    account.is_logged_in = False
    if account.session_info is not None:
        account.session_info.valid = False
    account.save_session(os.path.join(globalObject.cache_path, account.id + ".json"))


def get_account_info(account: Account) -> dict:
    response_json = {
        "id": account.id,
        "email": account.email,
        "is_logged_in": account.is_logged_in,
        "counter": account.counter.get(),
        "is_busy": account.is_busy,
        "is_disabled": account.is_disabled,
        "level": account.level,
        "user": None,
        "err": account.err_msg,
    }
    if account.session_info is not None:
        response_json["session"] = {
            "expires": account.session_info.expires,
        }
        response_json["user"] = {
            "id": account.session_info.user.id,
            "name": account.session_info.user.name,
            "email": account.session_info.user.email,
            "picture": account.session_info.user.picture,
            "image": account.session_info.user.image,
            "groups": account.session_info.user.groups,
        }
    return response_json


@app.route('/api/account/list')
def handle_get_account_list():
    result = []
    for account_id in globalObject.accounts.accounts:
        account = globalObject.accounts.accounts[account_id]
        result.append({
            "id": account.id,
            "email": account.email,
            "is_logged_in": account.is_logged_in,
            "counter": account.counter.get(),
            "is_busy": account.is_busy,
            "is_disabled": account.is_disabled,
            "level": account.level,
            "err": account.err_msg,
        })
    return flask.jsonify(result)


@app.route('/api/account/valid')
def handle_get_account_valid():
    level = int(flask.request.args.get('level', 1, type=int))
    result = []
    for account_id in globalObject.accounts.accounts:
        account = globalObject.accounts.accounts[account_id]
        if not account.is_logged_in:
            continue
        if account.is_disabled:
            continue
        if account.level > level:
            continue
        result.append({
            "id": account.id,
            "email": account.email,
            "is_logged_in": account.is_logged_in,
            "counter": account.counter.get(),
            "is_busy": account.is_busy,
            "is_disabled": account.is_disabled,
            "level": account.level,
            "err": account.err_msg,
        })
    return flask.jsonify(result)


@app.route('/api/account/dump')
def handle_get_account_dump():
    result = []
    for account_id in globalObject.accounts.accounts:
        account = globalObject.accounts.accounts[account_id]
        result.append(get_account_info(account))
    return flask.jsonify(result)


@app.route('/api/account', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def handle_get_account_info():
    if flask.request.method == 'GET':
        account_id = flask.request.args.get('account')
        account, r = get_account_query(account_id)
        if account is None:
            return r
        return flask.jsonify(get_account_info(account))
    elif flask.request.method == 'PUT':
        email = flask.request.args.get('email', "")
        password = flask.request.args.get('password', "")
        # 从 url 参数中获取 int 类型的 level，如果没有则返回 1
        level = int(flask.request.args.get('level', 65536, type=int))
        session_token = flask.request.get_data().decode()
        try:
            account = globalObject.accounts.apply(email, password, level, session_token, globalObject.config_path)
        except requests.RequestException as err:
            return flask.make_response(str(err), http.HTTPStatus.UNAUTHORIZED)
        except OpenAIAuth.Error as err:
            return flask.make_response(err.details, err.status_code)
        return flask.jsonify(get_account_info(account))
    elif flask.request.method == 'DELETE':
        account_id = flask.request.args.get('account')
        account, r = get_account_query(account_id)
        if account is None:
            return r
        del globalObject.accounts.accounts[account.id]
        return flask.jsonify({})
    elif flask.request.method == 'PATCH':
        # 修改帐号的 level
        account_id = flask.request.args.get('account')
        account, r = get_account_query(account_id)
        if account is None:
            return r
        level = int(flask.request.args.get('level', type=int))
        account.level = level
        globalObject.accounts.save(globalObject.config_path)
        return flask.jsonify(get_account_info(account))


@app.route('/api/account/login', methods=['PATCH', 'POST'])
def handle_account_login():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if account is None:
        return r
    if flask.request.method == 'POST':
        account.session_token = flask.request.get_data().decode()
        account_login_with_session_token(account)
    elif flask.request.method == 'PATCH':
        account_login_with_access_token(account)
        if not account.is_logged_in:
            account_login_with_session_token(account)
        if not account.is_logged_in:
            account_login_with_password(account)
    if not account.is_logged_in:
        return flask.make_response(account.err_msg, http.HTTPStatus.UNAUTHORIZED)
    globalObject.accounts.save(globalObject.config_path)
    return flask.jsonify(get_account_info(account))


@app.route('/api/account/disable', methods=['PATCH'])
def handle_account_disable():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id, False)
    if account is None:
        return r

    if not account.is_disabled:
        account.is_disabled = True
        globalObject.accounts.save(globalObject.config_path)
    return flask.jsonify(get_account_info(account))


@app.route('/api/account/enable', methods=['PATCH'])
def handle_account_enable():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if account is None:
        return r

    if account.is_disabled:
        account.is_disabled = False
        globalObject.accounts.save(globalObject.config_path)
    return flask.jsonify(get_account_info(account))
