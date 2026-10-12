# Documentation portal

The standalone Docsify portal publishes sidebar pages and pages linked from the earlier
Overview: one homepage, 17 guides, and 12 technical references in English. The sidebar
still lists 13 guides. Selected canonical `docs/` pages are
exported; other references open repository files on GitHub. The portal runs separately from
MCP and Swagger at `http://127.0.0.1:8080/`.

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
unmarked directory is preserved as a uniquely named `preserved-site-*` or
`preserved-staging-*` backup under `.local/docs-portal/`, then fresh output is created.
Backups are not served or automatically deleted. Symlink/junction paths are refused.

## Content ownership and publication

Edit website pages in `src/redmine_mcp_docs/guides/`; edit the homepage,
navigation, and cover alongside them. Sidebar links plus `OVERVIEW_GUIDES` and
`OVERVIEW_REFERENCES` in the exporter define the publication inventory.
Adding a Markdown file alone does not publish it. Remove source pages and update links
when removing entries. Required shell files, vendor notices, and the source maintenance
README remain; the README is not a website page.

The 2026-10-12 cleanup initially removed off-menu pages. At the user's follow-up request,
the pages directly linked from the earlier Overview were restored: module map, testing,
verification, visual examples, and 12 technical references. The
homepage's Technical references section provides access. The layout review remains removed.
Repository originals remain intact. The portal now publishes English only; all Vietnamese
source pages and language-switching support have been removed at the user's request.
Unpublished routes, including retired Vietnamese routes, resolve to the English 404 page.

The exporter copies current source contents, not only tracked files. Its manifest lists
the retained source documents relative to the repository root, with no copied code files.
The HEAD revision is informational and does not certify uncommitted content or acceptance.
Search inventories use the combined English publication inventory.
Export replaces the owned output directory to remove stale pages.

The portal source README documents navigation, media, local serving, and review handoff.
Keep canonical technical documentation in `docs/`. Retained references open locally;
other repository references open GitHub. Unpublished edits are not reflected on GitHub.

## Cover page

The [Docsify cover page](https://docsify.js.org/#/cover) uses `_coverpage.md`, included by the
exporter. The `/` landing route uses the cover through the `coverpage` setting in
`assets/portal.js`.
Other pages open directly.
Overview links in the sidebar and navbar use `/home.md`, opening
the homepage content directly. The landing route `/` retains the cover.
`onlyCover: false` keeps the homepage below the cover. The cover uses the local logo and
follows the portal's light and dark themes.
The portal reconciles cover visibility with the current landing route after navigation and
asynchronous cover rendering. Clicking an already active Overview link returns to the cover
at the top when its target is a landing route (for example the sidebar title); heading
links retain their section destinations. Browser back/forward navigation
keeps its normal scroll restoration. Browser verification of this fix remains pending.
The cover contains only the logo, product name, and short description, without buttons.
Installation links remain on the homepage and in the sidebar.
Shared screenshots remain in the homepage and client installation guide.
The homepage feature-plan example uses `assets/imgs/implement-stock-feature-example.png`
as a standalone figure without the Example session card or badge. A bounded scroll region
and a full-size link above the image support browsing and zooming. It replaces
the conversation reader; the unused reader script, transcript, and viewer-specific styles
have been removed from the source tree. Its existing heading link remains unchanged.
Browser review is still deferred.
Edit cover content in `src/redmine_mcp_docs/_coverpage.md`, and appearance through the
`--cover-*` variables in `assets/portal.css`. Local serving reloads edits automatically;
run `export` again before publishing a static copy.

## Documentation language

English is the only supported documentation language. Keep all Markdown and interface
messages in English. The exporter includes one homepage, 13 sidebar guides, four earlier
Overview guides, 12 technical references, and the required cover, navigation, and 404 files.
There is no language selector or translated route mapping. Export again and replace the
published output to remove previously generated Vietnamese pages and assets.

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

Never serve or upload the repository root. Export includes retained pages, required shell
files, and explicitly selected browser assets. Root documents, unlisted `docs/`, source code,
configuration templates, credentials, snapshots, and Git metadata are excluded.
Replace the deployed output directory when publishing so obsolete pages are removed.

## Verification handoff

The source README provides the maintenance handoff. When separately authorized, review
navigation, language switching, search, removed-route 404 behavior, stale-output removal,
offline assets, clipboard controls, themes, mobile layout, and subdirectory hosting.
No tests, browser checks, Inspector, or live calls are run automatically by export or serve.
MCP acceptance remains governed by the canonical [testing roadmap](testing-roadmap.md)
and [coverage matrix](plans/testing-coverage.md).
