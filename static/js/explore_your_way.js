// Auto-apply sidebar filters when a checkbox or the price slider changes.
(() => {
  const hiddenForm = document.getElementById('eyw-hidden-filters');
  if (!hiddenForm) return;
  const auto = () => hiddenForm.submit();
  hiddenForm.querySelectorAll('input[type="checkbox"]').forEach((box) => {
    box.addEventListener('change', auto);
  });
  const slider = document.querySelector('.eyw-price-slider');
  if (slider) {
    slider.addEventListener('change', () => {
      const url = new URL(window.location.href);
      url.searchParams.set('max_price', slider.value);
      window.location.assign(url.toString());
    });
    const label = document.querySelector('.eyw-price-labels span:last-child');
    if (label) {
      slider.addEventListener('input', () => { label.textContent = 'Rs ' + Number(slider.value).toLocaleString('en-MU'); });
    }
  }
})();
