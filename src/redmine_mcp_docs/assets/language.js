/* Locale is encoded in the hash, so shared links retain their language. */
(function () {
  'use strict';
  const vi = /^#\/vi(?:\/|$|\?)/.test(window.location.hash);
  const messages = vi ? {
    title: 'Tài liệu Redmine MCP', skip: 'Chuyển đến nội dung', loading: 'Đang tải tài liệu Redmine MCP...',
    language: 'Ngôn ngữ', appearance: 'Giao diện', auto: 'Tự động (hệ thống)', light: 'Sáng', dark: 'Tối',
    search: 'Tìm kiếm tài liệu', noData: 'Không tìm thấy tài liệu phù hợp',
    copy: 'Sao chép', copied: 'Đã sao chép', copyLabel: 'Sao chép đoạn mã', selectCopy: 'Chọn và sao chép',
    diagram: 'Cuộn để xem toàn bộ sơ đồ.', diagramLabel: 'Sơ đồ có thể cuộn',
    diagramError: 'Không thể hiển thị sơ đồ. Mã nguồn Mermaid:',
    resize: 'Thay đổi độ rộng menu', resizeHelp: 'Kéo để thay đổi độ rộng. Dùng phím trái/phải, Home/End hoặc nhấp đúp để đặt lại.',
    pixels: 'pixel', englishNotice: 'Trang này dùng tài liệu tiếng Anh gốc để giữ nguyên hợp đồng kỹ thuật và bằng chứng đã ghi nhận.',
  } : {
    title: 'Redmine MCP Documentation', skip: 'Skip to content', loading: 'Loading Redmine MCP documentation...',
    language: 'Language', appearance: 'Appearance', auto: 'Auto (system)', light: 'Light', dark: 'Dark',
    search: 'Search documentation', noData: 'No matching documentation',
    copy: 'Copy', copied: 'Copied', copyLabel: 'Copy code block', selectCopy: 'Select and copy',
    diagram: 'Scroll to explore the diagram.', diagramLabel: 'Scrollable diagram',
    diagramError: 'Diagram could not be rendered. Mermaid source:',
    resize: 'Resize navigation sidebar', resizeHelp: 'Drag to resize. Use Left/Right arrows, Home/End, or double-click to reset.',
    pixels: 'pixels', englishNotice: '',
  };
  document.documentElement.lang = vi ? 'vi' : 'en';
  document.title = messages.title;
  const translatedGuides = ['installation', 'first-calls', 'access', 'module-map', 'testing', 'verification', 'layout-review'];
  // Canonical routes with maintained local Vietnamese editions, without extensions.
  // Keep this registry synchronized with vi/ when adding or removing translations.
  const translatedPages = [
    'repository', 'CONTRIBUTING', 'CHANGELOG', 'SECURITY',
    'docs/configuration', 'docs/integrations/redmineup-tags',
    'docs/tool-reference', 'docs/manual-verification', 'docs/architecture',
    'docs/mcp-request-flow', 'docs/development', 'docs/workflows/redmine-tools',
    'docs/testing-roadmap', 'docs/plans/testing-coverage',
    'docs/testing/evidence/current-catalog-acceptance',
    'docs/testing/evidence/prep-022-026-testing', 'docs/testing/evidence/prep-027-testing',
    'docs/testing/evidence/tool-042-testing', 'docs/testing/evidence/tool-043-testing',
    'docs/operations', 'docs/test-data', 'docs/plans/index',
    'docs/reviews/documentation-state-audit-2026-10-09', 'docs/documentation-portal',
  ];
  function setupControl() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar || document.getElementById('portal-language')) return;
    const control = document.createElement('div');
    control.className = 'theme-control';
    const label = document.createElement('label');
    label.htmlFor = 'portal-language';
    label.textContent = messages.language;
    const select = document.createElement('select');
    select.id = 'portal-language';
    [['en', 'English'], ['vi', 'Tiếng Việt']].forEach(function (choice) {
      const option = document.createElement('option');
      option.value = choice[0];
      option.textContent = choice[1];
      select.appendChild(option);
    });
    select.value = vi ? 'vi' : 'en';
    select.addEventListener('change', function () {
      const path = window.location.hash.slice(1).split('?')[0].replace(/^\/vi(?=\/|$)/, '') || '/';
      const guide = /^\/guides\/([^/.]+)(?:\.md)?$/.exec(path);
      const target = guide && !translatedGuides.includes(guide[1]) ? '/' : path;
      // Translated headings differ, so omit the previous page's heading query.
      window.location.hash = '#' + (select.value === 'vi' ? '/vi' : '') + target;
      window.location.reload();
    });
    control.append(label, select);
    sidebar.appendChild(control);
  }
  window.portalLocale = { vi: vi, messages: messages, translatedPages: translatedPages, setupControl: setupControl };
  window.addEventListener('hashchange', function () {
    if (/^#\/vi(?:\/|$|\?)/.test(window.location.hash) !== vi) window.location.reload();
  });
  document.addEventListener('DOMContentLoaded', function () {
    const skip = document.querySelector('.skip-link');
    if (skip) skip.textContent = messages.skip;
    const loading = document.getElementById('app');
    if (loading && loading.getAttribute('role') === 'status') loading.textContent = messages.loading;
  });
}());
