import json
import uuid
import logging
import os

import requests

import OpenAIAuth.OpenAIAuth

# Disable all logging
logging.basicConfig(level=logging.ERROR)

BASE_URL = os.environ.get("CHATGPT_BASE_URL") or "https://chat.duti.tech/"

CHATGPT_DEFAULT_MODEL = "text-davinci-002-render-sha"


def login(email: str, password: str, proxy: str = None) -> str:
    auth = OpenAIAuth.OpenAIAuth.OpenAIAuth(
        email_address=email,
        password=password,
        proxy=proxy,
    )
    auth.begin()
    access_token = auth.get_access_token()
    return access_token


def login_with_cookie(session_token: str, proxy: str = None) -> str:
    auth = OpenAIAuth.OpenAIAuth.OpenAIAuth(
        email_address="",
        password="",
        proxy=proxy,
    )
    auth.session_token = session_token
    access_token = auth.get_access_token()
    return access_token


def get_session(access_token: str) -> requests.Session:
    session = requests.Session()
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
    return session


def get_conversations(session: requests.Session, offset=0, limit=20) -> requests.Response:
    url = BASE_URL + f"api/conversations?offset={offset}&limit={limit}"
    return session.get(url)


def delete_conversation(session: requests.Session, conversation_id: str) -> requests.Response:
    url = BASE_URL + f"api/conversation/{conversation_id}"
    return session.patch(url, data='{"is_visible": false}')


def clear_conversations(session: requests.Session) -> requests.Response:
    url = BASE_URL + "api/conversations"
    return session.patch(url, data='{"is_visible": false}')


def get_conversation_history(session: requests.Session, conversation_id: str) -> requests.Response:
    url = BASE_URL + f"api/conversation/{conversation_id}"
    return session.get(url)


def generate_title(session: requests.Session, conversation_id: str, message_id: str) -> requests.Response:
    url = BASE_URL + f"api/conversation/gen_title/{conversation_id}"
    data = {
        "message_id": message_id,
        "model": "text-davinci-002-render",
    }
    return session.post(url, data=json.dumps(data))


def change_title(session: requests.Session, conversation_id: str, title: str) -> requests.Response:
    url = BASE_URL + f"api/conversation/{conversation_id}"
    return session.patch(url, data=f'{{"title": "{title}"}}'.encode())


def get_models(session: requests.Session):
    url = BASE_URL + f"api/models"
    return session.get(url)


def send(session: requests.Session, conversation_id: str, parent_id: str,
         prompt: str, model: str = CHATGPT_DEFAULT_MODEL) -> requests.Response:
    data = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": {"content_type": "text", "parts": [prompt]},
            },
        ],
        "parent_message_id": parent_id,
        "model": model,
    }
    if conversation_id is not None and len(conversation_id) != 0:
        data["conversation_id"] = conversation_id
    return session.post(
        url=BASE_URL + "api/conversation",
        data=json.dumps(data),
        timeout=20,
        stream=True,
    )
