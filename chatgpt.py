import json
import os

import revChatGPT.V1

home_path = os.getenv("HOME")
config = json.load(open(os.path.join(home_path, ".config", "revChatGPT", "config.json")))
client = revChatGPT.V1.Chatbot(config=config)
