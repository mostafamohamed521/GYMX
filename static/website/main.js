document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.mobile-toggle');
  var menu = document.querySelector('.mobile-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      menu.classList.toggle('open');
    });
  }
});
