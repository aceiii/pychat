#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,invalid-name

from __future__ import division
from __future__ import print_function

import socketio
from flask import Flask, render_template

from random import randint
from hashlib import md5

GRAVATAR_URL = "http://www.gravatar.com/avatar/%s?s=64&d=identicon&r=PG"

sio = socketio.Server()
app = Flask(__name__)

users = {}

def get_value_or_default(obj, prop, default=None):
    if prop in obj:
        return obj[prop]
    return default

def iter_user_props(prop_name):
    return (get_value_or_default(u, prop_name) for u in users.itervalues())

def user_prop(sid, prop_name):
    return get_value_or_default(users[sid], prop_name)

def random_username():
    return "Guest" + str(randint(2**16, 2**32))

def is_unique_username(name):
    return not any(n == name for n in iter_user_props("name"))

def unique_random_username():
    while True:
        new_name = random_username()
        if is_unique_username(new_name):
            return new_name

def gravatar_for_username(username):
    name_hash = md5(username).hexdigest()
    return GRAVATAR_URL % (name_hash,)

def map_user(sid):
    return {
        "img": user_prop(sid, "avatar"),
        "username": user_prop(sid, "name"),
    }

@app.route("/")
def index():
    return render_template("index.html")

@sio.on("connect")
def connect(sid, env):
    print("connected:", sid)
    users[sid] = {"env": env}

@sio.on("disconnect")
def disconnect(sid):
    print("User disconnected. Clearing data for user", sid)
    del users[sid]

@sio.on("chat message")
def message(sid, data):
    print("message", sid, data)
    context = map_user(sid)
    context["message"] = data
    sio.emit("chat message", context)

@sio.on("client request_name")
def change_username(sid, new_name):
    if new_name and not is_unique_username(new_name):
        return

    new_avatar = None
    if not new_name:
        new_name = unique_random_username()
        new_avatar = gravatar_for_username(new_name)

    print("Setting name for", sid, "to", new_name)
    users[sid]["name"] = new_name
    if new_avatar:
        users[sid]["avatar"] = new_avatar
    sio.emit("server update_name", new_name, sid)

@sio.on("client get_users")
def get_users(sid):
    mapped_users = [map_user(sid) for sid in users]
    sio.emit("server users", mapped_users, sid)

flask_app = app
app = socketio.Middleware(sio, flask_app)

if __name__ == "__main__":
    import eventlet
    eventlet.wsgi.server(eventlet.listen(("", 3000)), app)

