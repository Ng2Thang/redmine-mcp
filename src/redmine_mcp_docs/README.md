# Redmine MCP documentation portal source

This directory contains the standalone Docsify shell, introductory guides, browser assets, and
export tooling. Detailed documentation remains canonical in the repository's `docs/` directory.
The portal uses the bundled Docsify Themeable Simple light theme. Customize Themeable variables
in `assets/portal.css`; configure its plugin in `assets/portal.js`.

Choose **Appearance** in the sidebar: **Light**, **Dark**, or **Auto (system)**.
Auto is the default and follows system appearance changes. The browser remembers your
choice for this portal; theme colors use local Themeable variable overrides in
`assets/portal.css`, with the preference applied by `assets/theme.js` before styles load.
Diagrams render again with the selected appearance when it changes.

On desktop, drag the sidebar's right edge to resize it. The browser remembers the width
for this portal. Focus the edge and use Left/Right arrows (Shift for larger steps) or
Home/End to reach the limits; double-click to restore the default width. Mobile uses
the standard fixed-width navigation drawer.

From Git Bash at the repository root:

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

The server defaults to `http://127.0.0.1:8080/`; `serve 8088` selects another port. It serves the
generated `.local/docs-portal/site/` directory. Restart after source changes. Do not serve the
repository root or open `index.html` through `file://`.

Read [maintenance and deployment](../../docs/documentation-portal.md) for the content ownership,
offline asset inventory, export boundaries, and hosting instructions. The
[manual checklist](guides/verification.md) is provided for a separately authorized check.
