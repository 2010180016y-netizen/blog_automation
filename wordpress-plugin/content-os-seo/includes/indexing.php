<?php
/**
 * Indexing Governance Logic
 *
 * Goals:
 * - Keep pre-QA or draft content out of index.
 * - Allow indexing/sitemap only when QA has passed.
 * - Auto-canonicalize duplicate/similar content via post meta.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Returns true if post is index-eligible by governance rules.
 *
 * Rules:
 * - Must be published
 * - Must have QA pass marker `_cos_qa_pass` = '1'
 * - Must not be force-noindexed via `_cos_noindex` = '1'
 */
function cos_seo_is_index_eligible( $post_id ) {
    $post = get_post( $post_id );
    if ( ! $post ) {
        return false;
    }

    if ( 'publish' !== $post->post_status ) {
        return false;
    }

    $qa_pass = get_post_meta( $post_id, '_cos_qa_pass', true );
    if ( '1' !== (string) $qa_pass ) {
        return false;
    }

    $force_noindex = get_post_meta( $post_id, '_cos_noindex', true );
    if ( '1' === (string) $force_noindex ) {
        return false;
    }

    return true;
}

/**
 * Render robots noindex for non-eligible content.
 */
function cos_seo_render_indexing_governance_meta() {
    if ( ! is_singular() ) {
        return;
    }

    $post_id = get_queried_object_id();
    if ( ! $post_id ) {
        return;
    }

    if ( ! cos_seo_is_index_eligible( $post_id ) ) {
        echo "<meta name=\"robots\" content=\"noindex,follow\" />\n";
    }
}

/**
 * Canonical override for duplicate/similar pages.
 *
 * `_cos_duplicate_of` can be:
 * - another post ID
 * - canonical URL
 */
function cos_seo_apply_duplicate_canonical( $canonical ) {
    if ( ! is_singular() ) {
        return $canonical;
    }

    $post_id = get_queried_object_id();
    if ( ! $post_id ) {
        return $canonical;
    }

    $duplicate_of = get_post_meta( $post_id, '_cos_duplicate_of', true );
    if ( empty( $duplicate_of ) ) {
        return $canonical;
    }

    if ( is_numeric( $duplicate_of ) ) {
        $target_permalink = get_permalink( (int) $duplicate_of );
        if ( ! empty( $target_permalink ) ) {
            return $target_permalink;
        }
    }

    if ( filter_var( $duplicate_of, FILTER_VALIDATE_URL ) ) {
        return $duplicate_of;
    }

    return $canonical;
}

/**
 * Exclude non-eligible entries from WP sitemap.
 */
function cos_seo_filter_sitemap_entry( $entry, $post, $post_type ) {
    if ( empty( $post->ID ) ) {
        return $entry;
    }

    if ( ! cos_seo_is_index_eligible( $post->ID ) ) {
        return false;
    }

    return $entry;
}

add_action( 'wp_head', 'cos_seo_render_indexing_governance_meta', 2 );
add_filter( 'cos_seo_canonical_url', 'cos_seo_apply_duplicate_canonical', 20 );
add_filter( 'wp_sitemaps_posts_entry', 'cos_seo_filter_sitemap_entry', 10, 3 );
