import json
import uuid

import requests
import revChatGPT.V1


def get_conversations(session: requests.sessions.Session, offset=0, limit=20) -> requests.Response:
    url = revChatGPT.V1.BASE_URL + f"api/conversations?offset={offset}&limit={limit}"
    return session.get(url)


def history(session: requests.sessions.Session, conversation_id: str) -> requests.Response:
    url = revChatGPT.V1.BASE_URL + f"api/conversation/{conversation_id}"
    return session.get(url)


def gen_title(session: requests.sessions.Session, conversation_id: str, message_id: str) -> requests.Response:
    url = revChatGPT.V1.BASE_URL + f"api/conversation/gen_title/{conversation_id}"
    data = {
        "message_id": message_id,
        "model": "text-davinci-002-render",
    }
    return session.post(url, data=json.dumps(data))


def change_title(session: requests.sessions.Session, conversation_id: str, title: str):
    url = revChatGPT.V1.BASE_URL + f"api/conversation/{conversation_id}"
    return session.patch(url, data=f'{{"title": "{title}"}}'.encode())


def send(session: requests.sessions.Session, config: dict, conversation_id: str, parent_id: str,
         prompt: str) -> requests.Response:
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
        "model": "text-davinci-002-render-sha"
        if not config.get("paid")
        else "text-davinci-002-render-paid",
    }
    if conversation_id is not None and len(conversation_id) != 0:
        data["conversation_id"] = conversation_id
    return session.post(
        url=revChatGPT.V1.BASE_URL + "api/conversation",
        data=json.dumps(data),
        timeout=360,
        stream=True,
    )
