function showPassword() {
  var inputPass = document.getElementById("password");
  var btnShowPass = document.getElementById("btn-password");

  if (inputPass.type === "password") {
    inputPass.setAttribute("type", "text");
    btnShowPass.setAttribute("src", "/static/assets/svg/invisible.svg");
  } else {
    inputPass.setAttribute("type", "password");
    btnShowPass.setAttribute("src", "/static/assets/svg/eye.svg");
  }
}
