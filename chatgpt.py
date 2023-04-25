import http
import json
import uuid
import os
import requests

import OpenAIAuth

BASE_URL = os.environ.get("CHATGPT_BASE_URL") or "https://bypass.churchless.tech/api/"
LOGIN_URL = "https://explorer.api.openai.com/api/auth/session"

CHATGPT_DEFAULT_MODEL = "text-davinci-002-render-sha"


class UserInfo:
    def __init__(self, user_json: dict):
        self.id: str = user_json['id']
        self.name: str = user_json['name']
        self.email: str = user_json['email']
        self.image: str = user_json['image']
        self.picture: str = user_json['picture']
        self.groups: list = user_json['groups']

    def asdict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'image': self.image,
            'picture': self.picture,
            'groups': self.groups,
        }


class SessionInfo:
    def __init__(self, session_json: dict):
        self.user: UserInfo = UserInfo(session_json['user'])
        self.expires: str = session_json['expires']
        self.access_token: str = session_json['accessToken']
        self.valid: bool = session_json.get('valid')

    def asdict(self) -> dict:
        return {
            'user': self.user.asdict(),
            'expires': self.expires,
            'accessToken': self.access_token,
            'valid': self.valid,
        }


def login(email: str, password: str, proxy: str = None) -> str:
    auth = OpenAIAuth.Authenticator(email, password, proxy)
    try:
        auth.login()
    except OpenAIAuth.Error as err:
        raise err
    return auth.session_token


def get_session_info(session_token: str, proxy: str = None) -> SessionInfo:
    auth = OpenAIAuth.Authenticator("", "", proxy)
    auth.session_token = session_token
    try:
        session_dict = auth.get_session_info()
    except OpenAIAuth.Error as err:
        raise requests.HTTPError(str(err))
    try:
        return SessionInfo(session_dict)
    except KeyError:
        raise requests.HTTPError("invalid session info")


def set_session(session: requests.Session, access_token: str):
    session.headers.clear()
    session.headers.update(
        {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Openai-Assistant-App-Id": "",
            "Connection": "close",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://chat.openai.com/chat",
        },
    )
    session.cookies.update(
        {
            "library": "revChatGPT",
        },
    )


def get_response_body_detail(response_body: bytes | dict) -> (str, int):
    if type(response_body) == bytes:
        try:
            response_json = json.loads(response_body)
        except json.decoder.JSONDecodeError:
            return None
    else:
        assert type(response_body) == dict
        response_json = response_body
    if response_json is None:
        return None
    detail = response_json.get("detail")
    if detail is None:
        return None
    if type(detail) != str:
        assert type(detail) == dict
        code = detail.get("code")
        message = detail.get("message")
        if code == 'token_expired':
            return message, http.HTTPStatus.UNAUTHORIZED
    detail_check = str(detail).lower()
    if detail_check.find('too many requests') >= 0:
        return detail, http.HTTPStatus.TOO_MANY_REQUESTS
    if detail_check.find('not found') >= 0:
        return detail, http.HTTPStatus.NOT_FOUND
    if detail_check.find('something went wrong') >= 0:
        return detail, http.HTTPStatus.NOT_ACCEPTABLE
    if detail_check.find('gone wrong') >= 0:
        return detail, http.HTTPStatus.NOT_ACCEPTABLE
    if detail_check.find('only one message at a time') >= 0:
        return detail, http.HTTPStatus.CONFLICT
    if detail_check.find('Access token is missing') >= 0:
        assert False  # access token is missing


def get_conversations(session: requests.Session, offset=0, limit=20) -> requests.Response:
    url = BASE_URL + f"conversations?offset={offset}&limit={limit}"
    return session.get(url)


def delete_conversation(session: requests.Session, conversation_id: str) -> requests.Response:
    url = BASE_URL + f"conversation/{conversation_id}"
    return session.patch(url, data='{"is_visible": false}')


def clear_conversations(session: requests.Session) -> requests.Response:
    url = BASE_URL + "conversations"
    return session.patch(url, data='{"is_visible": false}')


def get_conversation_history(session: requests.Session, conversation_id: str) -> requests.Response:
    url = BASE_URL + f"conversation/{conversation_id}"
    return session.get(url)


def generate_title(session: requests.Session, conversation_id: str, message_id: str) -> requests.Response:
    url = BASE_URL + f"conversation/gen_title/{conversation_id}"
    data = {
        "message_id": message_id,
        "model": "text-davinci-002-render",
    }
    return session.post(url, data=json.dumps(data))


def change_title(session: requests.Session, conversation_id: str, title: str) -> requests.Response:
    url = BASE_URL + f"conversation/{conversation_id}"
    return session.patch(url, data=f'{{"title": "{title}"}}'.encode())


def get_models(session: requests.Session, timeout: int | None = None):
    url = BASE_URL + f"models"
    return session.get(url, timeout=timeout)


def send(session: requests.Session, conversation_id: str, parent_id: str,
         prompt: str, model: str = CHATGPT_DEFAULT_MODEL) -> requests.Response:
    data = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "author": {
                    "role": "user"
                },
                "role": "user",
                "content": {
                    "content_type": "text",
                    "parts": [prompt],
                },
            },
        ],
        "parent_message_id": parent_id,
        "model": model,
    }
    if conversation_id is not None and len(conversation_id) != 0:
        data["conversation_id"] = conversation_id
    return session.post(
        url=BASE_URL + "conversation",
        data=json.dumps(data),
        timeout=600,
        stream=True,
    )
