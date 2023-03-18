import http
import os

import flask
import requests

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


def get_account_info(account: Account) -> dict:
    response_json = {
        "id": account.id,
        "email": account.email,
        "is_logged_in": account.is_logged_in,
        "counter": account.counter.get(),
        "is_busy": account.is_busy,
        "is_disabled": account.is_disabled,
        "user": None,
        "err": account.err_msg,
    }
    if account.session_info is not None:
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
            "err": account.err_msg,
        })
    return flask.jsonify(result)


@app.route('/api/account/valid')
def handle_get_account_valid():
    result = []
    for account_id in globalObject.accounts.accounts:
        account = globalObject.accounts.accounts[account_id]
        if not account.is_logged_in:
            continue
        if account.is_disabled:
            continue
        result.append({
            "id": account.id,
            "email": account.email,
            "is_logged_in": account.is_logged_in,
            "counter": account.counter.get(),
            "is_busy": account.is_busy,
            "is_disabled": account.is_disabled,
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


@app.route('/api/account', methods=['GET', 'PUT', 'DELETE'])
def handle_get_account_info():
    if flask.request.method == 'GET':
        account_id = flask.request.args.get('account')
        account, r = get_account_query(account_id)
        if account is None:
            return r
        return flask.jsonify(get_account_info(account))
    elif flask.request.method == 'PUT':
        session_token = flask.request.get_data().decode()
        try:
            account = globalObject.accounts.apply(session_token, globalObject.config_path)
        except requests.RequestException as err:
            return flask.make_response(str(err), http.HTTPStatus.UNAUTHORIZED)
        return flask.jsonify(get_account_info(account))
    elif flask.request.method == 'DELETE':
        account_id = flask.request.args.get('account')
        account, r = get_account_query(account_id)
        if account is None:
            return r
        del globalObject.accounts.accounts[account.id]
        return flask.jsonify({})


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
