<?php
/**
 * Helper Functions
 */

function cos_seo_get_current_url() {
    global $wp;
    return home_url( add_query_arg( array(), $wp->request ) );
}

function cos_seo_get_description_text() {
    $description = '';
    if ( is_singular() ) {
        $post = get_queried_object();
        $description = get_post_meta( $post->ID, '_cos_seo_description', true );
        if ( empty( $description ) ) {
            $description = wp_trim_words( $post->post_content, 30 );
        }
    } else {
        $description = get_bloginfo( 'description' );
    }
    return apply_filters( 'cos_seo_helper_description', $description );
}
