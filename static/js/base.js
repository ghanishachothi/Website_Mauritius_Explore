(() => {
  const track = document.getElementById('navTrack');
  const previous = document.getElementById('navPrev');
  const next = document.getElementById('navNext');
  const accountButton = document.querySelector('[data-dropdown-toggle="accountPanel"]');
  const accountPanel = document.getElementById('accountPanel');

  if (track && previous && next) {
    previous.addEventListener('click', () => track.scrollBy({ left: -track.clientWidth * 0.8, behavior: 'smooth' }));
    next.addEventListener('click', () => track.scrollBy({ left: track.clientWidth * 0.8, behavior: 'smooth' }));
  }

  if (!accountButton || !accountPanel) return;

  const closeAccount = () => {
    accountPanel.hidden = true;
    accountButton.setAttribute('aria-expanded', 'false');
  };

  accountButton.addEventListener('click', () => {
    const isOpen = accountButton.getAttribute('aria-expanded') === 'true';
    accountPanel.hidden = isOpen;
    accountButton.setAttribute('aria-expanded', String(!isOpen));
  });

  document.addEventListener('click', (event) => {
    if (!accountButton.contains(event.target) && !accountPanel.contains(event.target)) closeAccount();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeAccount();
  });
})();