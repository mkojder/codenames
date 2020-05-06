function inputBoxChange() {
  let inp0 = $("#input0");
  let inp1 = $("#input1");
  let inp2 = $("#input2");
  if ($.trim(inp0.val()) !== "" && $.trim(inp1.val()) !== "" && $.trim(inp2.val()) !== "") {
    $('#joinGame').prop('disabled', false);
  } else {
    $('#joinGame').prop('disabled', true);
  }
}

function joinGame() {
  let inp0 = $("#input0").val().toLowerCase();
  let inp1 = $("#input1").val().toLowerCase();
  let inp2 = $("#input2").val().toLowerCase();
  window.location.href = `game.html?id=game-${inp0}-${inp1}-${inp2}`;
  return false;
}

function newGame() {
  window.location.href = '/game.html';
  return false;
}

function keyEvent(e) {
  if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
      $('#submit-username').click();
      return false;
  } else {
      return true;
  }
}

$("#newGame").click(newGame);
$("#joinGame").click(joinGame);
$("#input0").keypress(keyEvent);
$("#input1").keypress(keyEvent);
$("#input2").keypress(keyEvent);

