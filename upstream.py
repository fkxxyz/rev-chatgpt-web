from revChatGPT.V1 import Chatbot, configure

if __name__ == "__main__":
    chatbot = Chatbot(configure())
    conversations = chatbot.get_conversations()
    print(conversations)
