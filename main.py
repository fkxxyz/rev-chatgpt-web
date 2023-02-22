#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import argparse
import http
import json
import os
import threading
import uuid
from typing import Iterator

import requests
import revChatGPT.V1
import flask

import patch

app = flask.Flask(__name__)


class GlobalObjectClass:
    def __init__(self):
        self.client: revChatGPT.V1.Chatbot = None
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


@app.route('/api/conversations')
def get_conversations():
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
    response = patch.get_conversations(globalObject.client.session, offset, limit)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


@app.route('/api/title', methods=['PATCH'])
def change_title():
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    title_bytes = flask.request.get_data()
    title_str = title_bytes.decode()
    if len(title_str) == 0:
        return flask.make_response('error: missing title body', http.HTTPStatus.BAD_REQUEST)
    response = patch.change_title(globalObject.client.session, conversation_id, title_str)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    try:
        response_json = json.loads(response.content)
    except json.decoder.JSONDecodeError:
        return flask.make_response(response.content, http.HTTPStatus.NOT_FOUND)
    return flask.jsonify(response_json)


@app.route('/api/title', methods=['POST'])
def gen_title():
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    message_id = flask.request.args.get('mid')
    if message_id is None or len(message_id) == 0:
        return flask.make_response('error: missing m`id query', http.HTTPStatus.BAD_REQUEST)
    response = patch.gen_title(globalObject.client.session, conversation_id, message_id)
    if response.status_code != http.HTTPStatus.OK:
        return flask.make_response(response.content, response.status_code)
    return flask.jsonify(json.loads(response.content))


@app.route('/api/history')
def get_history():
    conversation_id = flask.request.args.get('id')
    if conversation_id is None or len(conversation_id) == 0:
        return flask.make_response('error: missing id query', http.HTTPStatus.BAD_REQUEST)
    response = patch.history(globalObject.client.session, conversation_id)
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
            if line[:7] == b'event: ':
                event = line[7:]
                if event == 'ping':
                    pass
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
    response = patch.send(globalObject.client.session, app.config["auth_config"], conversation_id, parent_id, msg_str)
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


def run(host: str, port: int, dist: str, auth_config: dict):
    from waitress import serve

    app._static_folder = dist
    app.config["auth_config"] = auth_config
    print("login to ChatGPT ...")
    globalObject.client = revChatGPT.V1.Chatbot(config=app.config["auth_config"])
    print("login success")
    serve(app, host=host, port=port)


def main() -> int:
    home_path = os.getenv("HOME")
    parser = argparse.ArgumentParser(description="chatgpt web")
    parser.add_argument('--dist', '-d', type=str, help='ui dist path', default='./ui/dist')
    parser.add_argument('--host', '-o', type=str, help='host', default="127.0.0.1")
    parser.add_argument('--port', '-p', type=int, help='port', default=9987)
    parser.add_argument('--auth-config', '-c', type=str, help='revChatGPT config.json',
                        default=os.path.join(home_path, ".config", "revChatGPT", "config.json"))
    args = parser.parse_args()
    with open(args.auth_config, 'rb') as f:
        auth_config = json.load(f)
    run(args.host, args.port, args.dist, auth_config)
    return 0


if __name__ == "__main__":
    exit(main())
