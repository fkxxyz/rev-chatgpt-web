import http
import json
import threading
import uuid
from typing import Iterator

import flask
import requests

import chatgpt
from account import Account
from api.account_ import get_account_query, account_logout
from api import app
from api.common import globalObject

logged_out_code_set = {
    http.HTTPStatus.UNAUTHORIZED,
    http.HTTPStatus.FORBIDDEN,
}


@app.route('/api/models')
def handle_get_models():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id, False)
    if r is not None:
        return r
    response = chatgpt.get_models(account.session)
    if response.status_code != http.HTTPStatus.OK:
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    try:
        response_json = json.loads(response.content)
    except json.JSONDecodeError:
        return flask.make_response(response.content, http.HTTPStatus.INTERNAL_SERVER_ERROR)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
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
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/conversation', methods=['DELETE'])
def handle_delete_conversation():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) != 36:
        return flask.make_response('error: missing or invalid id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.delete_conversation(account.session, conversation_id)
    if response.status_code != http.HTTPStatus.OK:
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['PATCH'])
def handle_change_title():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) != 36:
        return flask.make_response('error: missing or invalid id query', http.HTTPStatus.BAD_REQUEST)
    title_bytes = flask.request.get_data()
    title_str = title_bytes.decode()
    if len(title_str) == 0:
        return flask.make_response('error: missing title body', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.change_title(account.session, conversation_id, title_str)
    if response.status_code != http.HTTPStatus.OK:
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['POST'])
def handle_gen_title():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) != 36:
        return flask.make_response('error: missing or invalid id query', http.HTTPStatus.BAD_REQUEST)
    message_id = flask.request.args.get('mid')
    if message_id is None or len(message_id) == 0:
        return flask.make_response('error: missing m`id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.generate_title(account.session, conversation_id, message_id)
    if response.status_code != http.HTTPStatus.OK:
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


@app.route('/api/history')
def handle_get_history():
    account_id = flask.request.args.get('account')
    account, r = get_account_query(account_id)
    if r is not None:
        return r
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) != 36:
        return flask.make_response('error: missing or invalid id query', http.HTTPStatus.BAD_REQUEST)
    response = chatgpt.get_conversation_history(account.session, conversation_id)
    if response.status_code != http.HTTPStatus.OK:
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        return flask.make_response(response.content, response.status_code)
    response_json = json.loads(response.content)
    r = chatgpt.get_response_body_detail(response_json)
    if r is not None:
        if r[1] == http.HTTPStatus.UNAUTHORIZED:
            account_logout(account, response)
        return flask.make_response(r[0], r[1])
    return flask.jsonify(response_json)


def get_reply(account: Account, response: requests.Response, response_iter: Iterator, mid: str):
    stopped_event = globalObject.stop_message_flag.get(mid)
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
                if "message" not in line_resp or line_resp["message"] is None:
                    print(line)
                    continue
                globalObject.messages[mid] = line_resp
                globalObject.messages[mid]["finished"] = False
                globalObject.messages[mid]["stopped"] = False
                globalObject.messages[mid]["error"] = ""
                if not stopped_event.is_set():
                    globalObject.messages[mid]["stopped"] = True
                    break
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
        stopped_event.set()
        del globalObject.stop_message_flag[mid]
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
        if response.status_code in logged_out_code_set:
            account_logout(account, response)
        r = chatgpt.get_response_body_detail(response.content)
        if r is not None:
            if r[1] == http.HTTPStatus.UNAUTHORIZED:
                account_logout(account, response)
            return flask.make_response(r[0], r[1])
        return flask.make_response(response.content, response.status_code)
    response_iter = response.iter_lines()
    try:
        for i in range(12):
            line: bytes = next(response_iter)
            if len(line) == 0:
                continue
            if line[:6] != b'data: ':
                r = chatgpt.get_response_body_detail(line)
                if r is not None:
                    if r[1] == http.HTTPStatus.UNAUTHORIZED:
                        account_logout(account, response)
                    return flask.make_response(r[0], r[1])
                continue
            try:
                line_resp = json.loads(line[6:])
            except json.decoder.JSONDecodeError:
                print(line)
                continue
            role = line_resp["message"]["author"]["role"]
            if role == "assistant":
                break
        else:
            return flask.make_response("assistant role not found", http.HTTPStatus.INTERNAL_SERVER_ERROR)
    except requests.RequestException as err:
        return flask.make_response(str(err), http.HTTPStatus.INTERNAL_SERVER_ERROR)
    role = line_resp["message"]["author"]["role"]
    if role != "assistant":
        return flask.make_response("assistant role not found", http.HTTPStatus.INTERNAL_SERVER_ERROR)
    line_resp["finished"] = False
    line_resp["error"] = ""
    new_mid = line_resp["message"]["id"]
    globalObject.messages[new_mid] = line_resp
    account.is_busy = True
    stopped_event = threading.Event()
    stopped_event.set()
    globalObject.stop_message_flag[new_mid] = stopped_event
    print("request " + new_mid, " opened")
    threading.Thread(target=get_reply, args=(account, response, response_iter, new_mid)).start()
    return flask.jsonify({"mid": line_resp["message"]["id"]})


@app.route('/api/get', methods=["GET", "PATCH"])
def handle_get():
    message_id = flask.request.args.get('mid')
    if message_id is None:
        return flask.make_response('error: missing mid query', http.HTTPStatus.BAD_REQUEST)
    if message_id not in globalObject.messages:
        return flask.make_response('error: no such mid: ' + message_id, http.HTTPStatus.NOT_FOUND)
    if flask.request.method == "PATCH":
        stopped_event = globalObject.stop_message_flag.get(message_id)
        if stopped_event is not None:
            stopped_event.clear()
            stopped_event.wait()
    return flask.jsonify(globalObject.messages[message_id])
