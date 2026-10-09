# Portal layout review

Review date: **2026-10-09**. The user explicitly requested a layout, CSS, and error
review after the Docsify Themeable implementation. These results apply to the sampled
pages in the working tree, not to every item in the [manual checklist](verification.md).

## Corrections

- Restored complete homepage card borders where the theme's link styling overrode them.
- Wrapped long sidebar labels instead of truncating them.
- Replaced three semicolons in the canonical request-flow sequence diagram's message
  text; Mermaid interpreted those semicolons as statement separators and failed to render.
- Limited large diagrams to a scrollable region with an explanatory caption, keyboard
  focus, and unrestricted height when printing.
- Prevented duplicate copy buttons, announced copy status, restored focus after the
  clipboard fallback, and selected code when automatic copying fails.
- Removed temporary Mermaid error containers when falling back to readable source.

## Observed results

A fresh headless Microsoft Edge profile loaded the generated portal from localhost.
The review disabled the browser cache and blocked external HTTP requests. Desktop
checks used a 1440-pixel viewport; mobile checks used 390- and 320-pixel viewports.

- Sampled home, installation, first calls, configuration, execution flow, module map,
  and audit pages rendered without page-wide horizontal overflow.
- The mobile sidebar opened successfully and long labels remained readable.
- Both execution-flow diagrams and the module-map diagram rendered without fallback.
- Search returned relevant results for `mutation uncertainty`.
- A configuration heading link resolved to its target; all twelve sampled raw source
  links returned HTTP 200.
- Code blocks had copy buttons. A trusted click copied the expected text, with Windows
  converting LF line endings to CRLF; comparison after newline normalization matched.
- The deliberately missing route displayed the custom missing-page screen. Its expected
  HTTP 404 was the only failed request in that navigation pass.
- No unhandled JavaScript exceptions or external asset requests were observed.

Local screenshots and JSON observations are retained in the ignored
`.local/docs-portal-review/` directory. They are not deployed with the portal.

## Verification limits

This was a sampled review in one headless browser. It did not verify Firefox, Safari,
physical touch devices, every navigation target, every highlighting language, clipboard
permission-denial behavior, invalid-diagram fallback, print output, or deployment to a
public domain or subdirectory. Export deletion and security-boundary scenarios remain
in the manual checklist. No unit, integration, E2E, Inspector, or live Redmine checks ran.
