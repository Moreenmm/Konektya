(function () {
  "use strict";
  // Communicates with CSS when JavaScript is running 
  document.documentElement.classList.add("js");

  // Mobile menu 
  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("main-nav");
    if (toggle && nav) {
      toggle.hidden = false;
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        toggle.textContent = open ? "Close menu" : "Menu";
      });
    }

    // Don't send an empty search  
    document.querySelectorAll("[data-search-form]").forEach(function (form) {
      var input = form.querySelector('input[type="search"]');
      var hint = form.querySelector("[data-search-hint]");
      if (!input || !hint) return;

      form.addEventListener("submit", function (e) {
        if (!input.value.trim()) {
            e.preventDefault();
            hint.textContent = "Please enter a search keyword.";
            hint.classList.add("is-error");
            input.setAttribute("aria-invalid", "true");
          input.focus();
        }
      });

      // Hide the message again as soon as the user starts typing.
      input.addEventListener("input", function () {
        if (input.value.trim()) {
          hint.textContent = "";
          hint.classList.remove("is-error");
          input.removeAttribute("aria-invalid");
        }
      });
    });

    // Moves focus to form error boxes
    var summary = document.querySelector("[data-focus-on-load]");
    if (summary) summary.focus();
  });
})();