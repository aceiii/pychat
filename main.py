#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,invalid-name

from __future__ import division
from __future__ import print_function

import socketio
from flask import Flask, render_template

import re
from random import randint
from hashlib import md5

GRAVATAR_URL = "//www.gravatar.com/avatar/%s?s=64&d=identicon&r=PG"
ALLOWED_USER_PROPS = ["username", "avatar"]

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
        "avatar": user_prop(sid, "avatar"),
        "username": user_prop(sid, "username"),
    }

def filter_user_data(data):
    new_data = {}
    for key in ALLOWED_USER_PROPS:
        if key in data:
            new_data[key] = data[key]
    return new_data

def is_valid_user_data(data):
    if len(data.keys()) < 1:
        return False
    if "username" in data and not is_unique_username(data["username"]):
        return False
    return True

def is_valid_avatar(avatar):
    if not avatar:
        return False
    if len(re.split(r"\s", avatar)) != 1:
        return False
    return True

def fix_avatar_url(avatar):
    fixed = avatar.strip()
    if fixed.find("http://") == 0:
        return fixed[5:]
    return fixed

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
    get_users()

@sio.on("chat message")
def message(sid, data):
    print("message", sid, data)
    context = map_user(sid)
    context["message"] = data
    sio.emit("chat message", context)

@sio.on("client update_profile")
def update_profile(sid, data):
    filtered_data = filter_user_data(data)
    if not is_valid_user_data(filtered_data):
        return
    for key in filtered_data:
        users[sid][key] = filtered_data[key]
    get_users()

@sio.on("client request_guest_profile")
def change_to_guest_profile(sid):
    new_name = unique_random_username()
    new_avatar = gravatar_for_username(new_name)

    print("Setting name for", sid, "to", new_name)
    print("Setting name for", sid, "to", new_avatar)

    users[sid]["username"] = new_name
    users[sid]["avatar"] = new_avatar

    sio.emit("server update_profile", map_user(sid), sid)
    get_users()

@sio.on("client request_name")
def change_username(sid, new_name):
    if not new_name or not is_unique_username(new_name):
        return
    print("Setting name for", sid, "to", new_name)
    users[sid]["username"] = new_name
    sio.emit("server update_profile", map_user(sid), sid)
    get_users()

@sio.on("client request_avatar")
def change_avatar(sid, new_avatar):
    if not is_valid_avatar(new_avatar):
        return

    users[sid]["avatar"] = fix_avatar_url(new_avatar)
    sio.emit("server update_profile", map_user(sid), sid)
    get_users()

@sio.on("client get_users")
def get_users(sid=None):
    print("fetching users for sid: %s" % (sid,))
    mapped_users = [map_user(s) for s in users]
    sio.emit("server users", mapped_users, sid)

flask_app = app
app = socketio.Middleware(sio, flask_app)

if __name__ == "__main__":
    import eventlet
    eventlet.wsgi.server(eventlet.listen(("", 3000)), app)

