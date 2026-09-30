/* ===== My Experiences page - Mauritius Explore =====
   Cancel / Edit / Delete / Favourite are real Django forms that reload the
   page. This file only handles the confirm boxes, View More, the star
   pickers, and the "Submit A Review" pop-up. */
(function () {
  var toastEl = document.getElementById('toast');
  var toastTimer;

  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 3500);
  }

  /* ---------- Show the message Django sent back after a redirect ---------- */
  var serverMessages = document.getElementById('serverMessages');
  if (serverMessages && serverMessages.children.length) {
    toast(serverMessages.children[0].textContent.trim());
  }

  /* ---------- Confirm before any form that asks for it ---------- */
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* ---------- View More / View Less ---------- */
  document.querySelectorAll('.view-more').forEach(function (btn) {
    var label = btn.firstChild;
    btn.addEventListener('click', function () {
      var block = btn.closest('.block');
      if (!block.querySelector('.is-extra')) {
        toast("That's everything for now.");
        return;
      }
      var open = block.classList.toggle('show-all');
      label.nodeValue = open ? 'View Less ' : 'View More ';
    });
  });

  /* ---------- Star pickers: light up as the radio buttons change ---------- */
  function paintPicker(picker, value) {
    picker.querySelectorAll('label.star').forEach(function (label) {
      label.classList.toggle('on', Number(label.dataset.value) <= value);
    });
  }
  document.querySelectorAll('.stars.picker').forEach(function (picker) {
    picker.addEventListener('change', function (e) {
      if (e.target.name === 'rating') paintPicker(picker, Number(e.target.value));
    });
  });

  /* ---------- Review cards: Edit shows the edit form, Edit again hides it ---------- */
  document.querySelectorAll('.edit-review').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.review-card');
      var form = card.querySelector('.review-edit-form');
      var opening = form.hidden;
      form.hidden = !opening;
      card.querySelector('.stars.read-only').hidden = opening;
      card.querySelector('.review-text').hidden = opening;
      btn.textContent = opening ? 'Cancel' : 'Edit';
      if (opening) form.querySelector('textarea').focus();
    });
  });

  /* ---------- Submit A Review pop-up ---------- */
  var modal = document.getElementById('reviewModal');
  var form = document.getElementById('reviewForm');
  var picker = document.getElementById('starPicker');

  function closeModal() { modal.hidden = true; }

  document.getElementById('openReview').addEventListener('click', function () {
    form.reset();
    paintPicker(picker, 0);
    modal.hidden = false;
    document.getElementById('reviewPlace').focus();
  });
  document.getElementById('closeReview').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });
})();