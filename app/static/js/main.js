/* Progressive enhancement only: every form here works as a normal POST if this
   file fails to load. The JS upgrades it to an inline submit. */
(function () {
  "use strict";

  // --- Mobile nav ---------------------------------------------------------
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
    });

    // Close the menu after following an in-page link.
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        toggle.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
      }
    });
  }

  // --- Async form submit --------------------------------------------------
  document.querySelectorAll("[data-async-form]").forEach(function (form) {
    var status = form.querySelector("[data-form-status]");
    var button = form.querySelector("button[type=submit]");
    var originalLabel = button ? button.textContent : "";

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (status) {
        status.textContent = "";
        status.className = "form__status";
      }
      if (button) {
        button.disabled = true;
        button.textContent = "Sending…";
      }

      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" }
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        })
        .then(function (result) {
          if (result.ok && result.data.success) {
            form.reset();
            show("Thanks — we got your message and will be in touch soon.", "is-success");
          } else {
            show(result.data.error || "Something went wrong. Please try again.", "is-error");
          }
        })
        .catch(function () {
          show("Could not reach the server. Please email us instead.", "is-error");
        })
        .finally(function () {
          if (button) {
            button.disabled = false;
            button.textContent = originalLabel;
          }
        });
    });

    function show(message, cls) {
      if (!status) return;
      status.textContent = message;
      status.className = "form__status " + cls;
    }
  });
})();
