import os
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()
application = app  # for WSGI servers

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)