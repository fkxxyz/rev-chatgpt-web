import argparse

from flask import Flask

app = Flask(__name__)


@app.route('/api/ping')
def api():
    return 'hello fkxxyz!'


@app.route('/')
def root():
    # 这里是你的根路径逻辑
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def static_proxy(path):
    # 这里是你的静态内容代理
    return app.send_static_file(path)


def run(host: str, port: int, dist: str):
    from waitress import serve

    app._static_folder = dist
    serve(app, host=host, port=port)


def main() -> int:
    parser = argparse.ArgumentParser(description="chatgpt web")
    parser.add_argument('--dist', '-d', type=str, help='ui dist path', default='./ui/dist')
    parser.add_argument('--host', '-o', type=str, help='host', default="127.0.0.1")
    parser.add_argument('--port', '-p', type=int, help='port', default=9987)
    args = parser.parse_args()
    run(args.host, args.port, args.dist)
    return 0


if __name__ == "__main__":
    exit(main())
