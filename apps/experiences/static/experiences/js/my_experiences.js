/* ===== My Experiences page - Mauritius Explore ===== */
document.addEventListener('DOMContentLoaded', function () {
  var toastEl = document.getElementById('toast');
  var toastTimer;

  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 3500);
  }

  /* ---------- Show server messages ---------- */
  var serverMessages = document.getElementById('serverMessages');
  if (serverMessages && serverMessages.children.length) {
    toast(serverMessages.children[0].textContent.trim());
  }

  /* ---------- Confirm before form submission ---------- */
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* ---------- View More / View Less Event Handling ---------- */
  document.querySelectorAll('.view-more').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var block = btn.closest('.block');
      if (!block) return;

      var extraItems = block.querySelectorAll('.is-extra');

      if (extraItems.length === 0) {
        toast("That's all for now.");

        var arrowSpan = btn.querySelector('.vm-arrow');
        btn.childNodes[0].nodeValue = "That's all for now ";
        if (arrowSpan) arrowSpan.style.display = 'none';

        setTimeout(function () {
          btn.childNodes[0].nodeValue = "View More ";
          if (arrowSpan) arrowSpan.style.display = 'inline-flex';
        }, 2500);
        return;
      }

      var isExpanded = block.classList.toggle('show-all');
      btn.childNodes[0].nodeValue = isExpanded ? 'View Less ' : 'View More ';

      if (!isExpanded) {
        toast("That's all for now.");
      }
    });
  });

  /* ---------- Star pickers ---------- */
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

  /* ---------- Review cards edit toggle ---------- */
  document.querySelectorAll('.edit-review').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.review-card');
      var form = card.querySelector('.review-edit-form');
      var readOnlyWrapper = card.querySelector('.read-only-content');

      var isFormHidden = form.hasAttribute('hidden');

      if (isFormHidden) {
        form.removeAttribute('hidden');
        if (readOnlyWrapper) readOnlyWrapper.setAttribute('hidden', '');
        btn.textContent = 'Cancel';
        var textarea = form.querySelector('textarea');
        if (textarea) textarea.focus();
      } else {
        form.setAttribute('hidden', '');
        if (readOnlyWrapper) readOnlyWrapper.removeAttribute('hidden');
        btn.textContent = 'Edit';
      }
    });
  });

  /* ---------- Modal handling ---------- */
  var modal = document.getElementById('reviewModal');
  var form = document.getElementById('reviewForm');
  var picker = document.getElementById('starPicker');

  function closeModal() { if (modal) modal.hidden = true; }

  var openBtn = document.getElementById('openReview');
  if (openBtn) {
    openBtn.addEventListener('click', function () {
      if (form) form.reset();
      if (picker) paintPicker(picker, 0);
      if (modal) modal.hidden = false;
      var input = document.getElementById('reviewPlace');
      if (input) input.focus();
    });
  }

  var closeBtn = document.getElementById('closeReview');
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (modal) {
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modal && !modal.hidden) closeModal();
  });
});