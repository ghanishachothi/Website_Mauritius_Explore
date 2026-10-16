(function () {
  "use strict";

  // Back button (top left)
  var back = document.querySelector("[data-back]");
  if (back) {
    back.addEventListener("click", function () {
      window.history.back();
    });
  }

  var form = document.querySelector(".checkout");
  if (!form) return;

  var radios = form.querySelectorAll(".method__input");
  var payMethod = document.getElementById("pay-method");
  var payButton = document.getElementById("pay-button");

  // Highlight the chosen payment row and update "Pay Rs 1,550 with ..."
  function sync() {
    radios.forEach(function (radio) {
      radio.closest(".method").classList.toggle("is-selected", radio.checked);
      if (radio.checked && payMethod) {
        payMethod.textContent = radio.getAttribute("data-short");
      }
    });
  }

  radios.forEach(function (radio) {
    radio.addEventListener("change", sync);
  });
  sync();

  // Stop double clicks from creating two bookings
  form.addEventListener("submit", function () {
    if (payButton) {
      payButton.disabled = true;
      payButton.classList.add("is-busy");
    }
  });
})();