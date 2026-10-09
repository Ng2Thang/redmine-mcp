/* Apply the saved appearance before styles load, without external dependencies. */
(function () {
  'use strict';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const storageKey = 'redmine-mcp-theme-' + new URL('./', window.location.href.split('#')[0]).pathname;
  const modes = ['auto', 'light', 'dark'];
  let mode = 'auto';
  try {
    const saved = localStorage.getItem(storageKey);
    if (modes.includes(saved)) mode = saved;
  } catch (_) { /* System appearance works when storage is disabled. */ }

  function apply() {
    const theme = mode === 'auto' ? (system.matches ? 'dark' : 'light') : mode;
    const changed = root.dataset.theme !== theme;
    root.dataset.theme = theme;
    root.dataset.themeMode = mode;
    const select = document.getElementById('portal-theme');
    if (select) select.value = mode;
    document.dispatchEvent(new CustomEvent('portal-theme-change', { detail: { changed: changed } }));
  }
  function setupControl() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar || document.getElementById('portal-theme')) return;
    const control = document.createElement('div');
    control.className = 'theme-control';
    const label = document.createElement('label');
    label.htmlFor = 'portal-theme';
    const messages = window.portalLocale.messages;
    label.textContent = messages.appearance;
    const select = document.createElement('select');
    select.id = 'portal-theme';
    [['auto', messages.auto], ['light', messages.light], ['dark', messages.dark]].forEach(function (choice) {
      const option = document.createElement('option');
      option.value = choice[0];
      option.textContent = choice[1];
      select.appendChild(option);
    });
    select.value = mode;
    select.addEventListener('change', function () {
      mode = select.value;
      try { localStorage.setItem(storageKey, mode); } catch (_) { /* Optional storage. */ }
      apply();
    });
    control.append(label, select);
    sidebar.appendChild(control);
  }
  system.addEventListener('change', function () { if (mode === 'auto') apply(); });
  window.addEventListener('storage', function (event) {
    if (event.key !== storageKey && event.key !== null) return;
    mode = modes.includes(event.newValue) ? event.newValue : 'auto';
    apply();
  });
  window.portalTheme = { setupControl: setupControl };
  apply();
}());
