(() => {
  const tabs = document.querySelectorAll('.experience-tab');
  const tabPanels = document.querySelectorAll('.experience-tab-panel');
  const mainImage = document.getElementById('main-gallery-img');
  const mainFigure = document.getElementById('main-gallery-image');
  const thumbs = document.querySelectorAll('.gallery-thumb[data-image]');
  const selectedPriceEl = document.getElementById('selected-price');
  const packageRadios = document.querySelectorAll('input[name="package"]');

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', (evt) => {
      if (evt.key !== 'Enter' && evt.key !== ' ') return;
      evt.preventDefault();
      activateTab(tab);
    });
  });

  function activateTab(tab) {
    tabs.forEach((t) => {
      const selected = t === tab;
      t.classList.toggle('is-active', selected);
      t.setAttribute('aria-selected', selected ? 'true' : 'false');
    });
    const targetId = tab.getAttribute('aria-controls');
    tabPanels.forEach((panel) => {
      const show = panel.id === targetId;
      panel.classList.toggle('is-visible', show);
      panel.hidden = !show;
    });
    if (tab.id && targetId) {
      const firstFocus = document.querySelector(`#${targetId} a, #${targetId} button`);
      if (firstFocus) firstFocus.setAttribute('tabindex', '-1');
    }
  }

  thumbs.forEach((thumb) => {
    const swap = () => {
      const url = thumb.getAttribute('data-image');
      if (!url || !mainImage) return;
      mainImage.src = url;
      thumbs.forEach((t) => t.classList.toggle('is-active', t === thumb));
    };
    thumb.addEventListener('click', swap);
    thumb.addEventListener('mouseenter', swap);
  });

  function formatPrice(value) {
    const num = Number(value || 0);
    return `Rs ${num.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }

  packageRadios.forEach((radio) => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.package-option').forEach((opt) => {
        const isSelected = opt.querySelector('input[name="package"]') === radio;
        opt.classList.toggle('is-selected', isSelected);
      });
      const price = radio.getAttribute('data-package-price');
      if (selectedPriceEl && price) selectedPriceEl.textContent = formatPrice(price);
    });
    if (radio.checked && selectedPriceEl) {
      const price = radio.getAttribute('data-package-price');
      if (price) selectedPriceEl.textContent = formatPrice(price);
    }
  });

  document.querySelectorAll('.info-text br, .info-text p').forEach(() => {});
})();
