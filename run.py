<<<<<<< HEAD
from app import create_app, socketio
=======
from app import create_app
from flask import Flask
>>>>>>> master

app = create_app()

if __name__ == '__main__':
<<<<<<< HEAD
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
=======
    app.run(host='0.0.0.0', port=5001, debug=True)
>>>>>>> master
