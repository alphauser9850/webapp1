import eventlet
eventlet.monkey_patch(all=True)

from app import create_app, socketio

app = create_app()
application = app  # for WSGI servers

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)