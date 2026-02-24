<?php
/**
 * Canonical URL Logic
 */

function cos_seo_render_canonical() {
    $canonical = '';

    if ( is_singular() ) {
        $canonical = get_permalink();
    } elseif ( is_front_page() ) {
        $canonical = home_url( '/' );
    } elseif ( is_category() || is_tag() || is_tax() ) {
        $canonical = get_term_link( get_queried_object() );
    }

    $canonical = apply_filters( 'cos_seo_canonical_url', $canonical );

    if ( ! empty( $canonical ) && ! is_wp_error( $canonical ) ) {
        echo '<link rel="canonical" href="' . esc_url( $canonical ) . '">' . "\n";
    }
}
