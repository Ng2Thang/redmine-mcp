/* Portal integration: local assets, hash routing, Mermaid, and accessible code copying. */
(function () {
  'use strict';

  const base = new URL('./', window.location.href.split('#')[0]);
  const messages = {
    search: 'Search documentation', noData: 'No matching documentation',
    copy: 'Copy', copied: 'Copied', copyLabel: 'Copy code block', selectCopy: 'Select and copy',
    diagram: 'Scroll to explore the diagram.', diagramLabel: 'Scrollable diagram',
    diagramError: 'Diagram could not be rendered. Mermaid source:',
    resize: 'Resize navigation sidebar',
    resizeHelp: 'Drag to resize. Use Left/Right arrows, Home/End, or double-click to reset.',
    pixels: 'pixels',
  };
  let diagramId = 0;
  let rendering = Promise.resolve();
  const diagramSources = new WeakMap();
  let activeDocument = new URL('home.md', base);

  window.mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: document.documentElement.dataset.theme === 'dark' ? 'dark' : 'neutral',
    fontFamily: 'Segoe UI, system-ui, sans-serif',
  });

  function escapeHtml(value) {
    return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (_) {
        // Some local browsers deny clipboard permissions; use the selection fallback.
      }
    }
    const field = document.createElement('textarea');
    const previousFocus = document.activeElement;
    field.value = text;
    field.className = 'clipboard-field';
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand('copy');
    field.remove();
    if (previousFocus instanceof HTMLElement) previousFocus.focus({ preventScroll: true });
    if (!copied) throw new Error('Clipboard unavailable');
  }

  function setupCoverNavigation() {
    const cover = document.querySelector('section.cover');
    if (!cover) return function () {};
    const landingHashes = ['#/'];
    const overviewHashes = ['#/home', '#/home.md'];

    function syncCover() {
      const hash = window.location.hash.split('?')[0] || '#/';
      const content = cover.querySelector('.cover-main');
      const visible = landingHashes.includes(hash) && Boolean(content && content.hasChildNodes());
      // Cover requests finish independently of page rendering. Reconcile their result
      // with the current route, including late responses after navigating away.
      if (cover.classList.contains('show') !== visible) cover.classList.toggle('show', visible);
      document.body.classList.toggle('sticky', !visible || cover.getBoundingClientRect().bottom <= 0);
    }

    const observer = new MutationObserver(syncCover);
    observer.observe(cover, {
      attributes: true,
      attributeFilter: ['class'],
      childList: true,
      subtree: true,
    });
    window.addEventListener('hashchange', syncCover);
    window.addEventListener('scroll', syncCover, { passive: true });
    window.addEventListener('resize', syncCover);
    document.addEventListener('click', function (event) {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
      const destination = new URL(link.href, window.location.href);
      if (destination.origin !== window.location.origin ||
          destination.pathname !== window.location.pathname ||
          destination.search !== window.location.search ||
          !landingHashes.concat(overviewHashes).includes(destination.hash) ||
          destination.hash !== window.location.hash) return;
      // An active homepage link needs an explicit scroll reset; its route controls the cover.
      event.preventDefault();
      window.scrollTo(0, 0);
      syncCover();
    });
    syncCover();
    return syncCover;
  }

  function setupSidebarResize() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar || document.querySelector('.sidebar-resizer')) return;
    const desktop = window.matchMedia('(min-width: 48em)');
    const storageKey = 'redmine-mcp-sidebar-width-' + base.pathname;
    const defaultWidth = 272;
    let preferredWidth = defaultWidth;
    let drag = null;
    try {
      const stored = Number(localStorage.getItem(storageKey));
      if (Number.isFinite(stored) && stored >= 240 && stored <= 480) preferredWidth = stored;
    } catch (_) { /* Resizing remains available when browser storage is disabled. */ }

    sidebar.id = sidebar.id || 'portal-sidebar';
    const handle = document.createElement('div');
    handle.className = 'sidebar-resizer';
    handle.tabIndex = 0;
    handle.setAttribute('role', 'separator');
    handle.setAttribute('aria-orientation', 'vertical');
    handle.setAttribute('aria-label', messages.resize);
    handle.setAttribute('aria-controls', sidebar.id);
    handle.title = messages.resizeHelp;
    document.body.appendChild(handle);

    function bounds() {
      return { min: 240, max: Math.max(240, Math.min(480, Math.floor(window.innerWidth * 0.45))) };
    }
    function applyWidth(value, save) {
      const limits = bounds();
      const width = Math.round(Math.max(limits.min, Math.min(limits.max, value)));
      document.documentElement.style.setProperty('--portal-sidebar-width', width + 'px');
      handle.setAttribute('aria-valuemin', String(limits.min));
      handle.setAttribute('aria-valuemax', String(limits.max));
      handle.setAttribute('aria-valuenow', String(width));
      handle.setAttribute('aria-valuetext', width + ' ' + messages.pixels);
      if (save) {
        preferredWidth = width;
        try { localStorage.setItem(storageKey, String(width)); } catch (_) { /* Optional storage. */ }
      }
      return width;
    }
    function finishDrag(event) {
      if (!drag || (event && event.pointerId !== drag.pointerId)) return;
      const pointerId = drag.pointerId;
      drag = null;
      document.body.classList.remove('sidebar-resizing');
      if (handle.hasPointerCapture(pointerId)) handle.releasePointerCapture(pointerId);
    }
    handle.addEventListener('pointerdown', function (event) {
      if (event.button !== 0 || !desktop.matches || drag) return;
      event.preventDefault();
      handle.focus({ preventScroll: true });
      drag = { pointerId: event.pointerId, x: event.clientX, width: sidebar.getBoundingClientRect().width };
      handle.setPointerCapture(event.pointerId);
      document.body.classList.add('sidebar-resizing');
    });
    handle.addEventListener('pointermove', function (event) {
      if (!drag || event.pointerId !== drag.pointerId) return;
      applyWidth(drag.width + event.clientX - drag.x, true);
    });
    handle.addEventListener('pointerup', finishDrag);
    handle.addEventListener('pointercancel', finishDrag);
    handle.addEventListener('lostpointercapture', finishDrag);
    handle.addEventListener('dblclick', function () { applyWidth(defaultWidth, true); });
    handle.addEventListener('keydown', function (event) {
      const width = Number(handle.getAttribute('aria-valuenow'));
      const step = event.shiftKey ? 40 : 10;
      const limits = bounds();
      const values = { ArrowLeft: width - step, ArrowRight: width + step, Home: limits.min, End: limits.max };
      if (!Object.prototype.hasOwnProperty.call(values, event.key)) return;
      event.preventDefault();
      applyWidth(values[event.key], true);
    });
    window.addEventListener('resize', function () {
      finishDrag();
      applyWidth(preferredWidth, false);
    });
    applyWidth(preferredWidth, false);
  }

  function renderDiagrams(diagrams) {
    // Serialize rendering and theme changes; retain source when replacing SVGs.
    rendering = rendering.then(async function () {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        theme: document.documentElement.dataset.theme === 'dark' ? 'dark' : 'neutral',
        fontFamily: 'Segoe UI, system-ui, sans-serif',
      });
      for (const element of diagrams) {
        if (!element.isConnected) continue;
        const source = diagramSources.get(element);
        if (source === undefined) continue;
        const renderId = 'portal-diagram-' + (++diagramId);
        try {
          const result = await window.mermaid.render(renderId, source);
          if (element.isConnected) {
            element.classList.remove('diagram-fallback');
            element.innerHTML = result.svg;
            const svg = element.querySelector('svg');
            if (svg && svg.viewBox.baseVal.width) {
              svg.style.minWidth = svg.viewBox.baseVal.width + 'px';
            }
            if (result.bindFunctions) result.bindFunctions(element);
          }
        } catch (_) {
          const temporary = document.getElementById('d' + renderId);
          if (temporary) temporary.remove();
          if (!element.isConnected) continue;
          element.classList.add('diagram-fallback');
          element.replaceChildren();
          const message = document.createElement('p');
          message.textContent = messages.diagramError;
          const pre = document.createElement('pre');
          pre.textContent = source;
          element.append(message, pre);
        }
      }
    }).catch(function () { /* Keep later route renders available. */ });
  }

  document.addEventListener('portal-theme-change', function (event) {
    if (event.detail.changed) renderDiagrams(Array.from(document.querySelectorAll('.mermaid')));
  });

  window.$docsify = {
    name: 'Redmine MCP',
    nameLink: '#/',
    homepage: 'home.md',
    coverpage: ['/'],
    onlyCover: false,
    basePath: base.pathname,
    routerMode: 'hash',
    relativePath: true,
    themeable: {
      readyTransition: true,
      responsiveTables: true,
    },
    loadSidebar: true,
    loadNavbar: true,
    mergeNavbar: true,
    subMaxLevel: 2,
    auto2top: true,
    noEmoji: true,
    executeScript: false,
    notFoundPage: '404.md',
    alias: {
      '/.*/_sidebar.md': '/_sidebar.md',
      '/.*/_navbar.md': '/_navbar.md',
    },
    noCompileLinks: [
      '.*\\.(py|sh|toml|ya?ml|json|rb|lock)([?#].*)?$',
      '(^|.*/)(LICENSE|\\.python-version|\\.env\\.example)([?#].*)?$',
    ],
    search: {
      paths: window.portalSearchPaths.en,
      namespace: 'redmine-mcp-docs-' + base.pathname + '-en-only-v5',
      maxAge: 60000,
      placeholder: messages.search,
      noData: messages.noData,
      depth: 4,
      hideOtherSidebarContent: false,
    },
    markdown: function (marked, renderer) {
      const originalCode = renderer.code.bind(renderer);
      const originalLink = renderer.link.bind(renderer);
      renderer.code = function (code, language) {
        if ((language || '').trim() === 'mermaid') {
          return '<div class="diagram-caption">' + escapeHtml(messages.diagram) + '</div>' +
            '<div class="diagram-block" role="region" aria-label="' + escapeHtml(messages.diagramLabel) + '" tabindex="0"><div class="mermaid">' +
            escapeHtml(code) + '</div></div>';
        }
        return originalCode(code, language);
      };
      renderer.link = function (href, title, text) {
        const isReference = /\.(py|sh|toml|ya?ml|json|rb|lock)([?#].*)?$/.test(href) ||
          /(^|\/)(LICENSE|\.python-version|\.env\.example)([?#].*)?$/.test(href);
        if (isReference && !/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(href)) {
          const destination = new URL(href, activeDocument);
          if (destination.pathname.startsWith(base.pathname)) href = destination.href;
        }
        return originalLink(href, title, text);
      };
      marked.setOptions({ renderer: renderer });
      return marked;
    },
    plugins: [function (hook, vm) {
      let syncCover = function () {};
      hook.mounted(function () { syncCover = setupCoverNavigation(); });
      hook.doneEach(function () { syncCover(); });
      hook.ready(setupSidebarResize);
      hook.ready(window.portalTheme.setupControl);
      hook.beforeEach(function (markdown) {
        let route = vm.route.path.replace(/^\//, '').replace(/\.md$/, '').replace(/\/$/, '') || 'home';
        activeDocument = new URL(route + '.md', base);
        return markdown;
      });
      // Docsify routes use ?id= for headings. Normalize GitHub-style #heading links
      // in generated HTML, leaving the canonical Markdown unchanged.
      hook.doneEach(function () {
        const content = document.querySelector('.markdown-section');
        if (!content) return;
        content.id = 'main';
        content.tabIndex = -1;
        document.querySelectorAll('.markdown-section a[href]').forEach(function (link) {
          const href = link.getAttribute('href');
          if (href && href.startsWith('#/') && href.indexOf('#', 1) !== -1) {
            const position = href.indexOf('#', 1);
            link.setAttribute('href', href.slice(0, position) + '?id=' + href.slice(position + 1));
          }
        });

        content.querySelectorAll('pre > code').forEach(function (code) {
          const pre = code.parentElement;
          if (pre.querySelector('.copy-code')) return;
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'copy-code';
          button.textContent = messages.copy;
          button.setAttribute('aria-label', messages.copyLabel);
          button.setAttribute('aria-live', 'polite');
          button.addEventListener('click', async function () {
            try {
              await copyText(code.textContent);
              button.textContent = messages.copied;
            } catch (_) {
              const selection = window.getSelection();
              if (selection) {
                const range = document.createRange();
                range.selectNodeContents(code);
                selection.removeAllRanges();
                selection.addRange(range);
              }
              button.textContent = messages.selectCopy;
            }
            window.setTimeout(function () { button.textContent = messages.copy; }, 2000);
          });
          pre.appendChild(button);
        });

        const diagrams = Array.from(content.querySelectorAll('.mermaid'));
        diagrams.forEach(function (element) {
          if (!diagramSources.has(element)) diagramSources.set(element, element.textContent);
        });
        renderDiagrams(diagrams);
      });
    }],
  };

  document.querySelector('.skip-link').addEventListener('click', function (event) {
    event.preventDefault();
    const content = document.getElementById('main');
    if (content) content.focus();
  });
}());
