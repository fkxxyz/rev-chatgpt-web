#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import argparse
import http
import json
import os
import threading
import uuid
from typing import Iterator, OrderedDict

import requests
import flask

import chatgpt
from account import Accounts, Account

app = flask.Flask(__name__)


class GlobalObjectClass:
    def __init__(self):
        self.accounts: OrderedDict[str, Account] = None
        self.default_account: Account = None
        # TODO 自动清理
        self.messages: dict = {}
        self.busy: bool = False


globalObject = GlobalObjectClass()


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def static_proxy(path):
    return app.send_static_file(path)


@app.route('/api/ping')
def api():
    return 'hello fkxxyz!'


@app.route('/api/accounts')
def get_accounts():
    result = []
    for account_id in globalObject.accounts:
        account = globalObject.accounts[account_id]
        result.append({
            "id": account.id,
            "email": account.email,
        })
    return flask.jsonify(result)


@app.route('/api/models')
def get_models():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    response = chatgpt.get_models(account.session)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


@app.route('/api/conversations')
def get_conversations():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    offset = flask.request.args.get('offset')
    limit = flask.request.args.get('limit')
    if offset is None or len(offset) == 0:
        offset = 0
    if limit is None or len(limit) == 0:
        limit = 20
    try:
        offset = int(offset)
        limit = int(limit)
    except ValueError:
        return flask.make_response('error: invalid offset or limit query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.get_conversations(account.session, offset, limit)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


@app.route('/api/title', methods=['PATCH'])
def change_title():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    title_bytes = flask.request.get_data()
    title_str = title_bytes.decode()
    if len(title_str) == 0:
        return flask.make_response('error: missing title body', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.change_title(account.session, conversation_id, title_str)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    try:
        response_json = json.loads(response.content)
    except json.decoder.JSONDecodeError:
        return flask.make_response(response.content, http.HTTPStatus.NOT_FOUND)
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['POST'])
def gen_title():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    message_id = flask.request.args.get('mid')
    if message_id is None or len(message_id) == 0:
        return flask.make_response('error: missing m`id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.generate_title(account.session, conversation_id, message_id)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


@app.route('/api/history')
def get_history():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.get_conversation_history(account.session, conversation_id)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


def get_reply(response: requests.Response, response_iter: Iterator, mid: str):
    try:
        for line in response_iter:
            if len(line) == 0:
                continue
            if line[:6] == b'data: ':
                try:
                    line_resp = json.loads(line[6:])
                except json.decoder.JSONDecodeError:
                    print(line)
                    continue
                globalObject.messages[mid] = line_resp
            elif line[:7] == b'event: ':
                event = line[7:]
                if event == 'ping':
                    print("ping")
                    pass
                else:
                    print(line)
            else:
                print(line)
    except requests.RequestException as e:
        globalObject.messages[mid]["error"] = str(e)
    finally:
        response.close()
        globalObject.busy = False
        globalObject.messages[mid]["finished"] = True
        print("request " + mid, " closed")


@app.route('/api/send', methods=['POST'])
def send():
    account = globalObject.default_account
    account_id = flask.request.args.get('account')
    if account_id is not None and len(account_id) != 0:
        account = globalObject.accounts.get(account_id)
        if account is None:
            return flask.make_response('error: no such account', http.HTTPStatus.NOT_FOUND)
    if globalObject.busy:
        return flask.make_response('error: server is busy', http.HTTPStatus.CONFLICT)
    conversation_id = flask.request.args.get('id')
    parent_id = flask.request.args.get('mid')
    if conversation_id is None:
        conversation_id = ''
    if parent_id is None:
        parent_id = ''
    if len(parent_id) == 0:
        if len(conversation_id) != 0:
            return flask.make_response('error: missing mid query', http.HTTPStatus.BAD_REQUEST)
        parent_id = str(uuid.uuid4())
    msg_bytes = flask.request.get_data()
    msg_str = msg_bytes.decode()
    try:
        response = chatgpt.send(account.session, conversation_id, parent_id, msg_str)
    except requests.exceptions.ReadTimeout as err:
        return flask.make_response(str(err), http.HTTPStatus.INTERNAL_SERVER_ERROR)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    response_iter = response.iter_lines()
    line = next(response_iter)
    if line[:6] != b'data: ':
        try:
            response_json = json.loads(line)
        except json.decoder.JSONDecodeError:
            return flask.make_response(line, http.HTTPStatus.BAD_REQUEST)
        if "detail" in response_json:
            detail = response_json["detail"]
            if type(detail) == str:
                detail_check = detail.lower()
                if detail_check.find('too many requests') >= 0:
                    return flask.make_response(detail, http.HTTPStatus.TOO_MANY_REQUESTS)
                if detail_check.find('not found') >= 0:
                    return flask.make_response(detail, http.HTTPStatus.NOT_FOUND)
                if detail_check.find('something went wrong') >= 0:
                    return flask.make_response(detail, http.HTTPStatus.NOT_ACCEPTABLE)
                if detail_check.find('gone wrong') >= 0:
                    return flask.make_response(detail, http.HTTPStatus.NOT_ACCEPTABLE)
                if detail_check.find('only one message at a time') >= 0:
                    return flask.make_response(detail, http.HTTPStatus.CONFLICT)
            else:
                return flask.make_response(str(detail), http.HTTPStatus.INTERNAL_SERVER_ERROR)
        return flask.make_response(line, http.HTTPStatus.BAD_REQUEST)
    line_resp = json.loads(line[6:])
    new_mid = line_resp["message"]["id"]
    globalObject.messages[new_mid] = line_resp
    globalObject.busy = True
    print("request " + new_mid, " opened")
    threading.Thread(target=get_reply, args=(response, response_iter, new_mid)).start()
    return flask.jsonify({"mid": line_resp["message"]["id"]})


@app.route('/api/get')
def get():
    message_id = flask.request.args.get('mid')
    if message_id is None:
        return flask.make_response('error: missing mid query', http.HTTPStatus.BAD_REQUEST)
    if message_id not in globalObject.messages:
        return flask.make_response('error: no such mid: ' + message_id, http.HTTPStatus.NOT_FOUND)
    return flask.jsonify(globalObject.messages[message_id])


def load_config(config: dict) -> Accounts:
    accounts = Accounts()
    accounts.load(config)
    return accounts


def cache_login(accounts: Accounts, cache_directory: str):
    for id_ in accounts.accounts:
        account = accounts.accounts[id_]
        access_token = ""
        try:
            with open(os.path.join(cache_directory, account.id + ".json"), 'rb') as f:
                account_cache = json.loads(f.read())
            access_token = account_cache.get("access_token")
        except FileNotFoundError:
            pass
        if len(access_token) == 0:
            account.login()
        else:
            account.login_with_token(access_token)
        if account.access_token != access_token:
            os.makedirs(cache_directory, 0o755, True)
            with open(os.path.join(cache_directory, account.id + ".json"), 'w') as f:
                f.write(json.dumps({
                    "access_token": account.access_token
                }))


def run(host: str, port: int, dist: str, config: dict, cache: str):
    from waitress import serve

    app._static_folder = dist
    print("login to ChatGPT ...")
    accounts = load_config(config)
    assert len(accounts.accounts) != 0
    cache_login(accounts, cache)
    globalObject.accounts = accounts.accounts
    for account_id in accounts.accounts:
        globalObject.default_account = accounts.accounts[account_id]
        break
    print("login success")
    serve(app, host=host, port=port)


def main() -> int:
    home_path = os.getenv("HOME")
    parser = argparse.ArgumentParser(description="chatgpt web")
    parser.add_argument('--dist', '-d', type=str, help='ui dist path', default='./ui/dist')
    parser.add_argument('--host', '-o', type=str, help='host', default="127.0.0.1")
    parser.add_argument('--port', '-p', type=int, help='port', default=9987)
    parser.add_argument('--config', '-c', type=str, help='revChatGPT config.json',
                        default=os.path.join(home_path, ".config", "revChatGPT", "config.json"))
    parser.add_argument('--cache', '-e', type=str, help='cache directory',
                        default=os.path.join(home_path, ".cache", "revChatGPT"))
    args = parser.parse_args()
    with open(args.config, 'rb') as f:
        config = json.load(f)
    run(args.host, args.port, args.dist, config, args.cache)
    return 0


if __name__ == "__main__":
    exit(main())
