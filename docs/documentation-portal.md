# Documentation portal

The standalone Docsify portal combines introductory pages from `src/redmine_mcp_docs/` with
canonical repository documentation from `docs/`. It runs separately from MCP and Swagger.
The default portal address is `http://127.0.0.1:8080/`; Swagger remains at `/docs` on the MCP server.

## Export and serve

Use Git Bash from the repository root. Git and Python 3.13 must be on PATH. The portal needs no
Python dependency installation, Docker, Node.js, Redmine connection, or API key.

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

`export` creates `.local/docs-portal/site/`. `serve` exports first and starts a foreground static
server bound to `127.0.0.1:8080`. An optional port changes the listener:

```bash
bash scripts/docs-portal.sh serve 8088
```

Press Ctrl+C to stop. Restart after editing documentation. If export is interrupted, the next
export replaces only marked staging/output directories under `.local/docs-portal/`. An existing
unmarked directory is refused rather than deleted. Symlink/junction paths are refused.

The export reads current working-tree contents of selected tracked documentation and explicitly
included new portal files. Other new canonical files under `docs/` should be added to Git before
export. `export-manifest.json` lists documents and linked repository references; its revision is
a reference to HEAD and does not certify uncommitted content or test acceptance.

## Content ownership

| Content | Edit here |
| --- | --- |
| Detailed installation/configuration/architecture/tool/testing/operations contracts | Canonical `docs/` files and root README |
| Introductory installation, first-call, access, module-map, and testing guides | `src/redmine_mcp_docs/guides/` |
| Portal homepage, sidebar, and navbar | `src/redmine_mcp_docs/home.md`, `_sidebar.md`, `_navbar.md` |
| Styling and Docsify/Mermaid integration | `src/redmine_mcp_docs/assets/portal.css` and `portal.js` |
| Appearance preference and startup theme | `src/redmine_mcp_docs/assets/theme.js` |
| Export allowlists and local server | `src/redmine_mcp_docs/tools/portal.py` |

Do not edit generated documentation in `.local/`. The exporter preserves canonical documents
at their repository-relative paths, so relative links between documentation pages remain valid.
The browser adapts heading links and source/configuration references for portal navigation.
Linked source/configuration files are copied only when tracked and within the explicit safe
reference roots or root-file allowlist. These references open directly rather than as Markdown.

Add new main pages to the sidebar for navigation and local search discovery. Evidence and task
records remain reachable through canonical document links. Preserve dates, exact verification
scope, waived stages, and pending acceptance; do not describe historical results as fresh checks.

## Offline browser assets

Docsify 4.13.1, its search plugin, Docsify Themeable 0.9.0, Mermaid 11.12.0, and Prism 1.29.0 components
are included under `src/redmine_mcp_docs/assets/vendor/`. The asset manifest records package
versions, registry archive integrity, local hashes, and modifications. Library license files and
original bundled legal notices are retained. The portal uses Themeable's **Simple light**
stylesheet as its base, local dark-mode variable overrides, and its plugin with system fonts,
local assets, and disabled emoji image expansion.

The sidebar's **Appearance** selector offers **Light**, **Dark**, and **Auto (system)**.
Auto is the default and follows live system appearance changes. The browser remembers the
choice for the portal's hosting path. `assets/theme.js` applies it before styles load and
falls back to system appearance if browser storage is unavailable. Mermaid diagrams render
again when the resolved appearance changes. No extra package or network request is needed.

Customize Themeable variables in `assets/portal.css`, including `--theme-color`,
`--base-font-family`, `--content-max-width`, `--sidebar-background`, and code/heading variables.
Portal-specific CSS covers homepage cards, diagrams, copy controls, and accessibility helpers.
The Themeable plugin is configured in `assets/portal.js` with readiness transitions and
responsive tables. Its CSS loads before portal overrides, and its plugin loads after Docsify.

Normal export and serving never download dependencies. Rendering, diagrams, syntax highlighting,
and local search are intended to work without Internet access. Browser JavaScript must be enabled,
and the directory must be served over HTTP; opening `index.html` as a local file is unsupported.
External reference links, dependency installation commands, and Redmine/Inspector workflows
still require their own network access.

To reacquire the pinned browser packages during an intentional maintenance task:

```bash
python src/redmine_mcp_docs/tools/vendor_assets.py
```

This command contacts npm and upstream license sources, validates downloaded package integrity,
and writes vendor assets/metadata. It does not install dependencies or run tests. Review asset
and license changes before committing. Upgrading pins is a separate maintenance decision.

## Static deployment

Export, then upload **only** the contents of `.local/docs-portal/site/` to your static host.
Keep the directory layout intact. The host should serve `index.html` for the directory and
appropriate JavaScript/CSS/SVG/text MIME types. Hash routing means deep links do not need an
SPA rewrite rule. Retain the generated `.nojekyll` file on hosts using Jekyll so the sidebar
and navbar files are served.

Root hosting and subdirectory hosting are supported by relative asset URLs and a base path
derived from the HTML location. Use a trailing slash for a subdirectory URL, for example
`https://example.test/redmine-mcp-docs/`. External publication is a separate action; this helper
does not deploy, create hosting resources, or contact a public service.

Never serve or upload the repository root. The export includes selected Markdown/image files,
portal assets, selected root documents, and allowed linked tracked text references. Credentials,
`.env`, snapshots, Git metadata, and unrelated private files are excluded. The shipped
`.env.example` can be included only when explicitly linked; it is a tracked template, not `.env`.
Review documentation for inappropriate content before publishing publicly.

## Verification handoff

The source contains a manual checklist at `src/redmine_mcp_docs/guides/verification.md`, shown
under Testing in the portal. It covers offline loading, clipboard behavior, highlighting,
diagrams, navigation, heading links, export refresh/removal, boundaries, mobile layout, and
root/subdirectory hosting. Portal-only checks need no Redmine fixtures or test dependencies.

Tests, browser checks, Inspector, live calls, and quality/testing tools are not automatically
executed by export or serve. Run them only within a separately authorized assignment and record
checks performed, deferred checks, failures, and limitations. MCP acceptance continues to use
the canonical [testing roadmap](testing-roadmap.md) and [coverage matrix](plans/testing-coverage.md).
