import http
import json
import threading
import uuid
from typing import Iterator

import flask
import requests

import chatgpt
from account import Account
from api.account_ import get_account_query
from api import app
from api.common import globalObject


@app.route('/api/models')
def handle_get_models():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    response = chatgpt.get_models(account.session)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account.is_logged_in = False
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/conversations')
def handle_get_conversations():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
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
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account.is_logged_in = False
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['PATCH'])
def handle_change_title():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
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
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account.is_logged_in = False
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['POST'])
def handle_gen_title():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    message_id = flask.request.args.get('mid')
    if message_id is None or len(message_id) == 0:
        return flask.make_response('error: missing m`id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.generate_title(account.session, conversation_id, message_id)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account.is_logged_in = False
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/history')
def handle_get_history():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.get_conversation_history(account.session, conversation_id)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account.is_logged_in = False
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


def get_reply(account: Account, response: requests.Response, response_iter: Iterator, mid: str):
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
        account.is_busy = False
        globalObject.messages[mid]["finished"] = True
        print("request " + mid, " closed")


@app.route('/api/send', methods=['POST'])
def handle_send():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    if account.is_busy:
        return flask.make_response('error: account is busy', http.HTTPStatus.CONFLICT)
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
        account.counter.increase()
        response = chatgpt.send(account.session, conversation_id, parent_id, msg_str)
    except requests.exceptions.ReadTimeout as err:
        return flask.make_response(str(err), http.HTTPStatus.INTERNAL_SERVER_ERROR)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    response_iter = response.iter_lines()
    line: bytes = next(response_iter)
    if line[:6] != b'data: ':
        r = chatgpt.get_response_body_detail(line)
        if r is not None:
            if r[1] == http.HTTPStatus.UNAUTHORIZED:
                account.is_logged_in = False
            return flask.make_response(r[0], r[1])
        return flask.make_response(line, http.HTTPStatus.INTERNAL_SERVER_ERROR)
    line_resp = json.loads(line[6:])
    new_mid = line_resp["message"]["id"]
    globalObject.messages[new_mid] = line_resp
    account.is_busy = True
    print("request " + new_mid, " opened")
    threading.Thread(target=get_reply, args=(account, response, response_iter, new_mid)).start()
    return flask.jsonify({"mid": line_resp["message"]["id"]})


@app.route('/api/get')
def handle_get():
    message_id = flask.request.args.get('mid')
    if message_id is None:
        return flask.make_response('error: missing mid query', http.HTTPStatus.BAD_REQUEST)
    if message_id not in globalObject.messages:
        return flask.make_response('error: no such mid: ' + message_id, http.HTTPStatus.NOT_FOUND)
    return flask.jsonify(globalObject.messages[message_id])