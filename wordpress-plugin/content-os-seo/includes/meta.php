<?php
/**
 * Meta Description Logic
 */

function cos_seo_render_meta_description() {
    $description = '';

    if ( is_singular() ) {
        $post = get_queried_object();
        $description = get_post_meta( $post->ID, '_cos_seo_description', true );
        
        if ( empty( $description ) ) {
            $description = wp_trim_words( $post->post_content, 30 );
        }
    } elseif ( is_front_page() ) {
        $description = get_bloginfo( 'description' );
    }

    $description = apply_filters( 'cos_seo_meta_description', $description );

    if ( ! empty( $description ) ) {
        echo '<meta name="description" content="' . esc_attr( $description ) . '">' . "\n";
    }
}
