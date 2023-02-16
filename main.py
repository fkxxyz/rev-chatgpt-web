#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import argparse
import http
import json
import os
import threading
import uuid

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
    conversations = globalObject.client.get_conversations()
    return flask.jsonify(conversations)


@app.route('/api/history')
def get_history():
    conversation_id = flask.request.args.get('id')
    history = globalObject.client.get_msg_history(conversation_id)
    return flask.jsonify(history)


def get_reply(response, response_iter):
    for line in response_iter:
        if len(line) == 0:
            continue
        if line[:6] == b'data: ':
            try:
                line_resp = json.loads(line[6:])
            except json.decoder.JSONDecodeError:
                print(line)
                continue
            globalObject.messages[line_resp["message"]["id"]] = line_resp
        else:
            print(line)
    response.close()
    globalObject.busy = False


@app.route('/api/send', methods=['POST'])
def send():
    if globalObject.busy:
        return flask.make_response('error: server is busy', http.HTTPStatus.SERVICE_UNAVAILABLE)
    conversation_id = flask.request.args.get('id')
    parent_id = flask.request.args.get('mid')
    if parent_id is None:
        if conversation_id is not None:
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
            if detail_check.find('something went wrong') >= 0:
                return flask.make_response(detail, http.HTTPStatus.NOT_ACCEPTABLE)
        return flask.make_response(line, http.HTTPStatus.BAD_REQUEST)
    line_resp = json.loads(line[6:])
    globalObject.messages[line_resp["message"]["id"]] = line_resp
    globalObject.busy = True
    print(msg_str)
    threading.Thread(target=get_reply, args=(response, response_iter)).start()
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
