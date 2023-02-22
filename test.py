import json
import os

import chatgpt

home_path = os.getenv("HOME")
config = json.load(open(os.path.join(home_path, ".config", "revChatGPT", "config.json")))
session_token = chatgpt.login_with_cookie(config["session_token"])
session = chatgpt.get_session(session_token)
