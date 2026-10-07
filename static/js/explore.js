(() => {
  const form = document.getElementById('experience-search');
  if (!form) return;

  const minimumSlider = document.getElementById('min-price-range');
  const maximumSlider = document.getElementById('max-price-range');
  const minimumInput = document.getElementById('search-min-price');
  const maximumInput = document.getElementById('search-max-price');
  const minimumLabel = document.getElementById('min-price-label');
  const maximumLabel = document.getElementById('max-price-label');
  const pricePreset = document.getElementById('price-preset');
  const rangeSlider = document.querySelector('.range-slider');
  const formatPrice = (value) => new Intl.NumberFormat('en').format(value);

  function updateRangeTrack() {
    if (!rangeSlider || !minimumSlider || !maximumSlider) return;
    const minimum = Number(minimumSlider.min);
    const maximum = Number(minimumSlider.max);
    const percentage = (value) => `${((value - minimum) / (maximum - minimum)) * 100}%`;
    rangeSlider.style.setProperty('--range-start', percentage(Number(minimumSlider.value)));
    rangeSlider.style.setProperty('--range-end', percentage(Number(maximumSlider.value)));
  }

  function syncPriceRange(changedSlider) {
    if (!minimumSlider || !maximumSlider || !minimumInput || !maximumInput) return;
    if (Number(minimumSlider.value) > Number(maximumSlider.value)) {
      if (changedSlider === minimumSlider) {
        maximumSlider.value = minimumSlider.value;
      } else {
        minimumSlider.value = maximumSlider.value;
      }
    }
    minimumInput.value = minimumSlider.value;
    maximumInput.value = maximumSlider.value;
    if (minimumLabel) minimumLabel.textContent = formatPrice(minimumSlider.value);
    if (maximumLabel) {
      maximumLabel.textContent = `${formatPrice(maximumSlider.value)}${maximumSlider.value === '10000' ? '+' : ''}`;
    }
    updateRangeTrack();
    if (pricePreset) pricePreset.value = '';
  }

  [minimumSlider, maximumSlider].forEach((slider) => {
    slider?.addEventListener('input', () => syncPriceRange(slider));
    slider?.addEventListener('change', () => {
      syncPriceRange(slider);
      form.requestSubmit();
    });
  });

  pricePreset?.addEventListener('change', () => {
    if (!minimumSlider || !maximumSlider) return;
    if (pricePreset.value) {
      const [minimum, maximum] = pricePreset.value.split(':');
      minimumSlider.value = minimum;
      maximumSlider.value = maximum;
    } else {
      minimumSlider.value = '0';
      maximumSlider.value = '10000';
    }
    syncPriceRange(maximumSlider);
    form.requestSubmit();
  });

  document.querySelector('[data-price-reset]')?.addEventListener('click', () => {
    if (!minimumSlider || !maximumSlider || !minimumInput || !maximumInput) return;
    minimumSlider.value = '0';
    maximumSlider.value = '10000';
    minimumInput.value = '0';
    maximumInput.value = '10000';
    if (minimumLabel) minimumLabel.textContent = '0';
    if (maximumLabel) maximumLabel.textContent = '10,000+';
    updateRangeTrack();
    if (pricePreset) pricePreset.value = '';
    form.requestSubmit();
  });

  document.querySelectorAll('[data-submit-on-change]').forEach((control) => {
    control.addEventListener('change', () => form.requestSubmit());
  });

  updateRangeTrack();
})();
