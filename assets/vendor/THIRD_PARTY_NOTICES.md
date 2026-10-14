# Third-party browser assets

The portal vendors the following packages. The adjacent `manifest.json` records exact versions,
upstream npm archive URLs/integrity values, local file hashes, and deliberate modifications.

| Package | Version | Source | License |
| --- | --- | --- | --- |
| Docsify | 4.13.1 | https://github.com/docsifyjs/docsify | MIT; `docsify/LICENSE` |
| Docsify Themeable | 0.9.0 | https://github.com/jhildenbiddle/docsify-themeable | MIT; `docsify-themeable/LICENSE` |
| Mermaid | 11.12.0 | https://github.com/mermaid-js/mermaid | MIT; `mermaid/LICENSE` |
| Prism | 1.29.0 | https://github.com/PrismJS/prism | MIT; `prismjs/LICENSE` |

Original copyright/license comments in bundled JavaScript are preserved. Bundled components
are distributed as part of the upstream browser builds; retain their legal comments when
updating or repackaging these files. The Mermaid IIFE bundle is self-contained for the diagrams
used here; the portal does not rely on remote module chunks or icon/font services.

Themeable's Simple light stylesheet and plugin are included without modifications.
Portal CSS customizes Themeable variables and chooses system fonts. Vendor acquisition is an
intentional online maintenance task;
ordinary export and serving use committed local files without downloading anything.
