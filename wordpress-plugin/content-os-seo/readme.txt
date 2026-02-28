=== Content OS SEO ===
Contributors: content-os
Tags: seo, technical seo, minimal, open graph, canonical
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0
License: GPLv2 or later

Minimal Technical SEO for Content OS.

== Description ==
This plugin provides essential SEO meta tags (Canonical, Open Graph, Twitter Cards, Meta Description) without the bloat of larger SEO suites.

== Installation ==
1. Upload the plugin folder to the `/wp-content/plugins/` directory.
2. Activate the plugin through the 'Plugins' menu in WordPress.

== Filters ==
- `cos_seo_meta_description`: Filter the meta description.
- `cos_seo_canonical_url`: Filter the canonical URL.
- `cos_seo_og_image`: Filter the OG image URL.


== Indexing Governance ==
- `_cos_qa_pass` = `1`: marks content index-eligible.
- `_cos_noindex` = `1`: force noindex even if published.
- `_cos_duplicate_of`: canonical target post ID or URL for duplicate/similar pages.
- Non-eligible posts are rendered with `noindex,follow` and excluded from WP sitemap entries.


== Consent Mode + CMP ==
- For EEA/UK/CH traffic, the plugin sets Google Consent Mode defaults to `denied` and renders a minimal consent banner.
- For non-target regions, consent defaults to `granted`.
- The banner persists state in `localStorage`/cookie key `cos_consent_v1` and updates Consent Mode via `gtag('consent', 'update', ...)`.
- Region detection uses `CF-IPCountry`, `GEOIP_COUNTRY_CODE`, or `X-Country-Code` headers if present.

== Consent Filters ==
- `cos_seo_consent_enabled`: enable/disable consent system.
- `cos_seo_consent_regions`: override target country code list (default: EEA/UK/CH).
