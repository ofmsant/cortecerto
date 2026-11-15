// Evita envio duplicado: depois do primeiro envio de um formulário marcado com
// data-evitar-duplo, novos envios são ignorados e os botões ficam desabilitados.
// A proteção real contra duplicidade continua no servidor.
(function () {
  "use strict";

  document.addEventListener("submit", function (evento) {
    var formulario = evento.target;
    if (!(formulario instanceof HTMLFormElement)) {
      return;
    }
    if (!formulario.hasAttribute("data-evitar-duplo")) {
      return;
    }
    if (formulario.getAttribute("data-enviando") === "true") {
      evento.preventDefault();
      return;
    }
    formulario.setAttribute("data-enviando", "true");
    formulario.querySelectorAll('button[type="submit"]').forEach(function (botao) {
      botao.classList.add("disabled");
      botao.setAttribute("aria-disabled", "true");
    });
  });

  // Ao voltar pelo histórico do navegador, libera os formulários novamente.
  window.addEventListener("pageshow", function (evento) {
    if (!evento.persisted) {
      return;
    }
    document.querySelectorAll("form[data-evitar-duplo]").forEach(function (formulario) {
      formulario.removeAttribute("data-enviando");
      formulario.querySelectorAll('button[type="submit"]').forEach(function (botao) {
        botao.classList.remove("disabled");
        botao.removeAttribute("aria-disabled");
      });
    });
  });
})();