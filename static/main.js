
var socket = io();
$("form").submit(function () {
    socket.emit("chat message", $("#input").val());
    $("#input").val("");
    return false;
});
socket.on("chat message", function(msg) {
    $("#messages").append($("<li>").text(msg));
});

