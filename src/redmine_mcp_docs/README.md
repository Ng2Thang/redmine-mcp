# Redmine MCP documentation portal

This directory contains the English-only Docsify website, browser
assets, and export tooling. Published pages include `_sidebar.md`
entries plus pages linked directly from the earlier Overview: one homepage, 17 guides,
and 12 technical references. The sidebar still lists 13 guides.

## Content boundaries

The sidebar and `OVERVIEW_GUIDES` / `OVERVIEW_REFERENCES` in `tools/portal.py` form the
publication inventory. New Markdown files are not automatically published.
When removing a sidebar entry, delete its source page and update links to it.

Required shell files remain: `index.html`, the homepage, navigation files, cover page,
and 404 page. The homepage is always exported.
This maintenance README is not exported as a page. Vendor license notices and manifests
remain required assets. Selected canonical pages from `docs/` are exported.
Root documents and other technical pages remain internal.
Links to references outside the publication inventory open repository files on GitHub.
Local unpublished edits become visible there only after publication to the repository.
Removed routes have no redirects and resolve to the 404 page.

`assets/search-paths.js` is generated from the combined publication inventory.
Search indexes English pages only. Do not edit generated files.
All Markdown must remain English. Use Git Bash commands and redact example secrets.

Keep `guides/installation.md`, `guides/testing.md`, and `guides/troubleshooting.md` aligned
with the canonical setup/test guides in `docs/` and the actual launchers. Built-in development
and E2E profiles share versioned projects but use different seed/evidence state. Preserve
dated verification results when updating instructions; a new setup description is not new
acceptance evidence. Edit source Markdown, not exported copies or generated search paths.

## Local serving and export

From Git Bash at the repository root:

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

The default URL is `http://127.0.0.1:8080/`. Use `serve 8088` for another port.
Serve only `.local/docs-portal/site/`, never the repository root. Export replaces
the owned output directory, removing obsolete pages. Source and asset edits trigger
export and browser reload. Restart after changing the exporter or launcher.
Static hosting must replace old output as well.
Publish the exported site, not this source directory: export also copies retained canonical
`docs/` pages and generates the search inventory.

If an output directory is missing its ownership marker, export moves it to a unique
`preserved-site-*` or `preserved-staging-*` backup under `.local/docs-portal/` before
creating fresh output. Backups are not served or automatically deleted. Inspect them
before removing them manually. Symlink and junction paths are still refused.

## Navigation and media

Keep onboarding, workflows, access, write actions, help, and Contributors in the sidebar.
Top navigation links to the same pages. Preserve heading IDs when editing content.
Theme controls support Light, Dark, and Auto. Sidebar width and appearance persist.
Desktop sidebar resizing supports dragging and keyboard controls.

The cover contains only the logo, product name, and description. Homepage and client
setup screenshots are shared from `assets/imgs/`. Keep credentials obscured and update
captions and alt text when changing media. Update the explicit exporter asset inventory.
The retained visual examples guide uses the shared illustrations in `assets/examples/`.
The homepage's Technical references section links to the earlier Overview's pages.
Overview navigation opens `/home.md` directly at the
content. The landing route `/` retains the cover for initial visits.

## Review handoff

Tests and browser verification require separate authorization. When assigned, review
navigation, English-only controls and search, old-route 404 behavior, and stale-output removal.
Documentation cleanup does not establish runtime acceptance.
