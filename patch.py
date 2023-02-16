import json
import uuid

import requests
import revChatGPT.V1


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
        "conversation_id": conversation_id,
        "parent_message_id": parent_id,
        "model": "text-davinci-002-render-sha"
        if not config.get("paid")
        else "text-davinci-002-render-paid",
    }
    return session.post(
        url=revChatGPT.V1.BASE_URL + "api/conversation",
        data=json.dumps(data),
        timeout=360,
        stream=True,
    )
