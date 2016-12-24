#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,invalid-name

from __future__ import division
from __future__ import print_function

import socketio
import eventlet
from flask import Flask, render_template

sio = socketio.Server()
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@sio.on("connect")
def connect(sid, env):
    print("connect", sid, env)

@sio.on("chat message")
def message(sid, data):
    print("message", sid, data)
    sio.emit("chat message", "%s:%s" % (sid, data))

@sio.on("disconnect")
def disconnect(sid):
    print("disconnect", sid)

if __name__ == "__main__":
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(("", 3000)), app)

