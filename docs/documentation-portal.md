# Documentation portal

The standalone Docsify portal combines user guides from `src/redmine_mcp_docs/` with
canonical repository documentation from `docs/`. English navigation prioritizes connection,
installation, everyday workflows, write access, and troubleshooting. Technical material
remains available through the contributor hub. It runs separately from MCP and Swagger.
The default portal address is `http://127.0.0.1:8080/`; Swagger remains at `/docs` on the MCP server.

## Export and serve

Use Git Bash from the repository root. Git and Python 3.13 must be on PATH. The portal needs no
Python dependency installation, Docker, Node.js, Redmine connection, or API key.

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

`export` creates `.local/docs-portal/site/`. `serve` exports first and starts a foreground
server bound to `127.0.0.1:8080`, polling documentation and assets for changes every second.
After a successful re-export, open browser pages reload automatically, preserving the current
route. Responses disable browser caching during local serving. An optional port changes the listener:

```bash
bash scripts/docs-portal.sh serve 8088
```

Press Ctrl+C to stop. Source edits do not require a restart; changes to the exporter Python code
or launcher script still require restarting the command. Live reload is injected only by `serve`
and is not included in static exports. If export is interrupted, the next
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
| User onboarding, workflows, access, troubleshooting, and contributor hub | `src/redmine_mcp_docs/guides/` |
| Portal cover, homepage, sidebar, and navbar | `src/redmine_mcp_docs/_coverpage.md`, `home.md`, `_sidebar.md`, `_navbar.md` |
| Visual tool examples and replacement media | `src/redmine_mcp_docs/guides/visual-examples.md` and `assets/examples/` |
| Styling and Docsify/Mermaid integration | `src/redmine_mcp_docs/assets/portal.css` and `portal.js` |
| Appearance preference and startup theme | `src/redmine_mcp_docs/assets/theme.js` |
| Vietnamese pages and navigation | `src/redmine_mcp_docs/vi/` |
| Language selection and interface messages | `src/redmine_mcp_docs/assets/language.js` |
| Export allowlists and local server | `src/redmine_mcp_docs/tools/portal.py` |

Do not edit generated documentation in `.local/`. The exporter preserves canonical documents
at their repository-relative paths, so relative links between documentation pages remain valid.
The browser adapts heading links and source/configuration references for portal navigation.
Linked source/configuration files are copied only when tracked and within the explicit safe
reference roots or root-file allowlist. These references open directly rather than as Markdown.

Add new main pages to the sidebar for navigation and local search discovery. Evidence and task
records remain reachable through canonical document links. Preserve dates, exact verification
scope, waived stages, and pending acceptance; do not describe historical results as fresh checks.

## User-guide content map (2026-10-12)

| Earlier entry point | Updated destination or treatment |
| --- | --- |
| Homepage focused on installation, execution flow, and testing | User overview with connect/setup paths, three prompts, workflows, and help |
| Installation as the only starting path | `guides/get-started.md` for existing-server users; installation retains its URL for server setup |
| First REST and MCP calls | Same `guides/first-calls.md` URL, with optional REST/Inspector examples after client onboarding |
| Access configuration | Same `guides/access.md` URL, with user guidance followed by administrator prerequisites |
| Visual examples and media replacement instructions | Existing visual guide remains a walkthrough; media maintenance moves to the source README |
| Detailed tool reference as the primary usage entry | `guides/workflows.md` and four core task guides, plus `guides/reference.md` for exact-contract links |
| Architecture, development, testing, evidence, operations, and maintenance sidebar groups | `guides/contributors.md` links to existing pages without moving or deleting routes |
| Error handling spread across technical references | `guides/troubleshooting.md` with symptoms, fixes, and FAQ |

The four core guides cover assigned issues, issue summaries, time reports, and issue creation.
Installation submenus now lead directly to client types (Codex, VS Code Copilot, Cursor, and
other clients) or server setups (local Python, sample Docker, and Docker with existing Redmine).
Shared prerequisites stay in each introduction; client identity and project discovery use
one first request. Workflow instructions and portal serving remain in their dedicated guides.
Backlog filters and progress drafts are variations in the issue-list guide; notes and time
logging are short follow-ups in the issue-summary and time-report guides. The standalone
`project-backlog`, `progress-update`, `update-issue`, and `log-time` pages were removed;
their old routes resolve to consolidated guides through Docsify aliases. The Everyday workflows
sidebar label opens the overview directly, replacing the separate Choose a workflow entry.
Each core guide introduces its goal and prerequisites, then uses three task-focused submenu
headings for the main action, variations or follow-ups, and troubleshooting. Prompts, steps,
illustrative results, and related tools remain within those sections as content rather than
separate submenu entries. New guides live directly under `guides/` so the existing export glob
includes them without changing the exporter. New Markdown is English, and documented
commands remain Bash.

Access and write actions keeps two destinations at their existing URLs: Choose your connection
and Make and review changes. The access page has two submenu sections for reader/writer choice
and administrator setup. The write page has three for checking access, making a change, and
reading the outcome. Candidate-action discovery appears once, and walkthrough links remain
within the action section. Writer admission, operation gates, native permissions, and uncertain
outcomes retain their existing contracts. This navigation change has not been browser-verified.

Help and reference now has two entries: Fix problems and find answers, and REST and Inspector
examples. Troubleshooting groups symptoms under Connection and access, Inputs and results,
and Frequently asked questions. Individual symptom anchors remain available as level-three
headings. REST/Inspector connection values stay in the introduction, leaving three sections
for Inspector, REST, and understanding results. Contributors opens the hub directly with
three sections for development, testing/evidence, and operations. Runtime settings and
Security policy move from the help menu to the contributor operations table; their canonical
URLs remain unchanged. Historical evidence remains linked in a collapsible list. These menu
changes have not been browser-verified.

The refresh changes documentation only. It does not establish new operation acceptance or
resolve existing waivers. Export, serving, browser checks, link-check tooling, tests, Inspector,
and live calls were not run for this change. The updated manual checklist is a verification
handoff requiring separate authorization. The existing Vietnamese edition is retained but
has not been synchronized with this English refresh.

## Cover page

The [Docsify cover page](https://docsify.js.org/#/cover) uses `_coverpage.md`, included by the
exporter. The English cover is shared by the `/`, `/vi`, and `/vi/` landing routes through the
`coverpage` setting and a Vietnamese cover alias in `assets/portal.js`. Other pages open directly.
`onlyCover: false` keeps the homepage below the cover. The cover uses the local logo and
follows the portal's light and dark themes.
The portal reconciles cover visibility with the current landing route after navigation and
asynchronous cover rendering. Clicking an already active Overview link returns to the cover
at the top; heading links retain their section destinations. Browser back/forward navigation
keeps its normal scroll restoration. Browser verification of this fix remains pending.
The cover contains only the logo, product name, and short description, without buttons.
Installation links remain on the homepage and in the sidebar.
Examples, screenshots, and animations belong in the user guides rather than on the cover.
Their assets remain exported for those guides.
The homepage feature-plan example uses `assets/imgs/implement-stock-feature-example.png`
as a standalone figure without the Example session card or badge. A bounded scroll region
and a full-size link above the image support browsing and zooming. It replaces
the conversation reader; the unused reader script, transcript, and viewer-specific styles
have been removed from the source tree. Its existing heading link remains unchanged.
Browser review is still deferred.
Edit cover content in `src/redmine_mcp_docs/_coverpage.md` and appearance through the
`--cover-*` variables in `assets/portal.css`. Local serving reloads edits automatically;
run `export` again before publishing a static copy.

## Vietnamese edition

Choose **Language → Tiếng Việt** in the sidebar or open `http://127.0.0.1:8080/#/vi/`.
The Vietnamese edition translates the interface, navigation, homepage, introductory guides,
portal checklist, and all 24 main reference pages linked from its sidebar. Detailed Vietnamese
editions reorganize or summarize longer material; the English originals remain authoritative
for complete contracts, scenario tables, commit histories, and evidence ledgers. Each local
reference edition links to its original. Dates, pending acceptance, waivers, and verification
limits remain explicit. Untranslated task records still use English source with a notice.

The existing Vietnamese edition predates the English user-guide refresh of 2026-10-12.
It is retained without changes; its navigation and content are not synchronized with the
new workflows. New Markdown remains English under the current repository instructions.
Any separately authorized translation update must maintain the registry in `assets/language.js`.
Exact local aliases precede the English fallback. Switching language preserves translated
page routes and drops heading
queries because translated headings differ. Language is encoded in the hash URL, with
separate search caches; themes and the saved sidebar width remain shared. Export includes
only Markdown from the dedicated translation tree, using the existing path boundary checks.

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

The source contains a manual checklist at `src/redmine_mcp_docs/guides/verification.md`, linked
from the contributor hub. Its 2026-10-12 handoff covers both onboarding paths, four core workflow
pages, prompts, navigation/search, retained technical routes, and the existing locale boundary.
The broader checklist covers offline loading, clipboard behavior, highlighting, diagrams,
heading links, export refresh/removal, boundaries, mobile layout, and root/subdirectory hosting.
Portal-only checks need no Redmine fixtures or test dependencies.

Tests, browser checks, Inspector, live calls, and quality/testing tools are not automatically
executed by export or serve. Run them only within a separately authorized assignment and record
checks performed, deferred checks, failures, and limitations. MCP acceptance continues to use
the canonical [testing roadmap](testing-roadmap.md) and [coverage matrix](plans/testing-coverage.md).
