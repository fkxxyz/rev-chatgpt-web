from api import app


@app.route('/')
def handle_root():
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def handle_static_proxy(path):
    return app.send_static_file(path)


@app.route('/api/ping')
def handle_api():
    return 'hello fkxxyz!'
