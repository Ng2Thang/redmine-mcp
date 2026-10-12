# Redmine MCP documentation portal source

This directory contains the standalone Docsify shell, user guides, browser assets, and
export tooling. The English portal follows the journey: understand the product, connect or
install, complete a first request, then use everyday workflows. Detailed contracts and
contributor documentation remain canonical in the repository's `docs/` directory.
The portal uses the bundled Docsify Themeable Simple light theme. Customize Themeable variables
in `assets/portal.css`; configure its plugin in `assets/portal.js`.

Choose **Appearance** in the sidebar: **Light**, **Dark**, or **Auto (system)**.
Auto is the default and follows system appearance changes. The browser remembers your
choice for this portal; theme colors use local Themeable variable overrides in
`assets/portal.css`, with the preference applied by `assets/theme.js` before styles load.
Diagrams render again with the selected appearance when it changes.

The **Language** selector switches between English and the existing Vietnamese edition in
`vi/`. This refresh updates English content only, following the current English-only Markdown
requirement. The Vietnamese navigation and pages predate the user-guide refresh and are not
synchronized with the new workflows. Existing translations are retained at their URLs.
New untranslated guides switch to the Vietnamese homepage through the language selector.
A future explicitly authorized translation update must maintain `assets/language.js`.
Locale is carried in shared hash URLs; search indexes are separated by language, while
appearance and sidebar width are shared.

## Content conventions

Use **MCP client installation** for setting up an AI application or extension and connecting
it to an existing server. Use **MCP server installation** for installing and running the
Redmine MCP service with Python or Docker. These are the two Get started entries.
The top navigation groups both pages under an **Install** dropdown.
Installation pages use level-two headings for client or server types so the sidebar submenu
leads directly to a setup choice. Keep shared prerequisites in the introduction. Combine
identity and project discovery into one first request, and link to workflow guides for next steps.
Portal serving belongs in the maintenance guide rather than the MCP server installation submenu.
Keep **REST and Inspector examples** under Help and reference as optional material.
Preserve existing page URLs when changing labels.

Start with the user's goal and prerequisites in the introduction, followed by a copyable prompt.
Workflow pages use three task-specific level-two headings: the main action, variations or
follow-ups, and troubleshooting. Keep how-it-works steps, example results, and related tools
as bold labels within those sections so they do not add submenu entries.
The Everyday workflows sidebar group links directly to the workflow overview; do not add
a duplicate Choose a workflow entry. Label synthetic results, resolve IDs through actual tools, and explain
visibility, pagination, or write uncertainty when they affect the task. Document Bash commands.
Link to canonical contracts rather than copying implementation histories into user flows.

Access and write actions has two entries: **Choose your connection** (`guides/access.md`)
and **Make and review changes** (`guides/write-actions.md`). The access guide groups connection
choices and administrator setup into two submenu headings. The write guide uses three:
Check your access, Make a change, and Read the outcome. Keep shared prerequisites in the
introduction and walkthrough links within the main action section. Document candidate-action
discovery in the write guide once; retain native permission checks and uncertain-outcome guidance.

Help and reference has two entries: **Fix problems and find answers** and **REST and Inspector
examples**. Troubleshooting uses three submenu headings for Connection and access, Inputs
and results, and Frequently asked questions. Keep individual symptoms as level-three headings
to preserve their anchors without adding submenu entries. Connection values introduce the
REST/Inspector guide rather than appearing as a separate submenu step.

The **Contributors** sidebar link opens the contributor hub directly, without an extra child
entry. Its three sections cover Develop tools, Testing and evidence, and Operate and maintain
the server. Runtime settings and Security policy remain accessible from the operations table;
recorded evidence stays in a collapsible list. Keep canonical document URLs unchanged.

Place **Supported tools** directly after Overview in the English sidebar,
linking to the existing `guides/reference.md` URL. Keep it out of the top navigation. The Overview also features
this page before the installation cards so readers can discover capabilities first.
The English sidebar then prioritizes onboarding, four everyday workflows, write access, and help.
Keep issue discovery, issue understanding, time reporting, and issue creation as the core
guides. Backlog filters and progress drafts are variations in the issue-list guide; notes
and time logging are short follow-ups in the issue-summary and time-report guides. The four
removed standalone routes resolve to their consolidated guides through `assets/portal.js`.
Architecture, development, testing, evidence, operations, and maintenance remain reachable
through `guides/contributors.md`; their original routes are preserved. New top-level guide
Markdown is exported automatically by the existing `guides/*.md` inventory.

## Example media maintenance

The Codex extension setup screenshot lives in `assets/imgs/install_mcp_codex_vscode_ext.png`
and is displayed in `guides/get-started.md`. It is explicitly included in `tools/portal.py`.
Keep credential values obscured when replacing the screenshot, and update its steps, caption,
and alt text if the interface changes.

Media lives in `assets/examples/`. Replace SVG mockups with sanitized screenshots and replace
`issue-flow.gif` plus its matching reduced-motion still `issue-flow.png` together. Keep existing
filenames, or update the guide and explicit asset inventory in `tools/portal.py`.
Update captions, alt text, and the animation transcript to describe actual captures. Until
then, retain illustrative-data notices. Never publish API keys or session tokens.

Keep the cover minimal: logo, product name, and short description, without buttons.
Installation links belong on the homepage and in the sidebar; example media belongs in the guides.

## Portal controls and local serving

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

## Homepage example screenshot

The Overview's **Explore a feature plan in Redmine** section uses
`assets/imgs/implement-stock-feature-example.png`, explicitly included in the exporter.
Keep its heading unchanged to preserve existing section links. The original 1920 × 13212
image remains intact, displayed at the content width within a bounded, keyboard-focusable
scroll region. The image stands on its own, without an Example session label or enclosing
card. A wrapping caption row places a prominent full-size link above the image so readers
can open the original in a new tab for browser zoom before scrolling.

Directly below it, `assets/imgs/example_redmine_tool.png` shows the resulting Redmine issue
list with development and test tasks. Both images appear before the product introduction,
use the same responsive figure styling and full-size action, and are explicitly exported.

Keep the section concise: a short description, screenshot, and viewing hint. Preserve alt
text and image dimensions when replacing it. The obsolete conversation viewer, transcript,
and viewer-specific styles have been removed. No AI or Redmine calls occur when viewing
the example. Browser review is deferred until separately authorized.

