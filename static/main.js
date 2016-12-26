
var $messages = $("#messages");
var $input = $("#input");
var $form = $("form");

var socket = io();
var user = {};

var templates = {
    chat_message: _.template($("#template-chat-message").html()),
};

function append_chat_message(context) {
    $messages.append(templates.chat_message(context));
}

function append_server_message(context) {
    $messages.append($("<li class='server-message'>").text(context.message));
}

$form.submit(function () {
    socket.emit("chat message", $input.val());
    $input.val("");
    $messages[0].scrollTo(0, $messages[0].scrollHeight);
    return false;
});

socket.on("connect", function() {
    console.log("Connected to chat server.");
    append_server_message({ message: "Connected to server." });
    var name = user.name || "";
    socket.emit("client request_name", name);
});

socket.on("disconnect", function() {
    console.log("Disconnected from chat server.");
    append_server_message({ context: "Disconnected from server." });
});

socket.on("chat message", function(context) {
    console.log(context);
    append_chat_message(context);
});

socket.on("server update_name", function(name) {
    console.log("Setting username to: ", name)
    append_server_message({ message: "Setting username to: " + name });
    user.name = name;
});

