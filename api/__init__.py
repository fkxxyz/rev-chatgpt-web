import flask

app = flask.Flask(__name__)

from api.account_ import *
from api.chatgpt_ import *
from api.index import *
