
var $messages = $("#messages");
var $users = $("#users");
var $input = $("#input");
var $form = $("form");

var socket = io();
var user = {};

var templates = {
    chat_message: _.template($("#template-chat-message").html()),
    user_item: _.template($("#template-user-item").html()),
};

var commands = {
    "/change_name": function (cmd_args) {
        if (cmd_args.length != 2) {
            return false;
        }
        socket.emit("client request_name", cmd_args[1]);
        return true;
    },
    "/change_avatar": function (cmd_args) {
        if (cmd_args.length != 2) {
            return false;
        }
        socket.emit("client request_avatar", cmd_args[1]);
        return true;
    },
    "/users": function (cmd_args) {
        if (cmd_args.length != 1) {
            return false;
        }
        socket.emit("client get_users");
        return true;
    },
};

function append_chat_message(context) {
    $messages.append(templates.chat_message(context));
}

function append_server_message(context) {
    $messages.append($("<li class='server-message'>").text(context.message));
}

function clear_input() {
   $input.val("");
}

function scroll_to_last_message() {
    _.defer(function () {
        $messages.scrollTop($messages[0].scrollHeight);
    });
}

function recreate_user_list(users) {
    $users.html("");
    _.forEach(users, function (user) {
        console.log(user);
        $users.append(templates.user_item(user));
    });
}

function is_command_string(cmd_str) {
    return cmd_str[0] === "/";
}

function is_valid_command(cmd) {
    return commands.indexOf(cmd) > -1;
}

function do_command(cmd_args) {
    var cmd = cmd_args[0].toLowerCase();
    var cmd_func = commands[cmd];
    return cmd_func && cmd_func(cmd_args);
}

function handle_command(cmd_str) {
    var cmd_args = _.filter(cmd_str.split(" "), function (c) { return c !== "" });
    if (!do_command(cmd_args)) {
        append_server_message({ class: "error", message: "Invalid command." });
    }
}

function handle_message(msg) {
    socket.emit("chat message", msg);
}

$form.submit(function () {
    var msg = $input.val().trim();
    clear_input();
    if (is_command_string(msg)) {
        handle_command(msg);
    } else if (msg) {
        handle_message(msg);
    }
    return false;
});

socket.on("connect", function () {
    console.log("Connected to chat server.");
    append_server_message({ message: "Connected to server." });
    var name = user.username || "";
    if (!name) {
        socket.emit("client request_guest_profile");
    } else {
        socket.emit("client update_profile", user);
    }
});

socket.on("disconnect", function () {
    console.log("Disconnected from chat server.");
    append_server_message({ message: "Disconnected from server." });
});

socket.on("chat message", function (context) {
    console.log(context);
    append_chat_message(context);
    scroll_to_last_message();
});

socket.on("server update_profile", function (data) {
    user = data
    console.log("Setting username to: ", user.username)
    append_server_message({ message: "Setting username to: " + user.username });
});

socket.on("server users", function (users) {
    console.log("Got new list of users:", users);
    recreate_user_list(users);
});

