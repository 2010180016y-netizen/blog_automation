<?php
/**
 * Plugin Name: Content OS A/B Test
 * Description: Minimal A/B Testing for CTA buttons.
 * Version: 1.0.0
 * Author: Content OS Team
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'COS_AB_PATH', plugin_dir_path( __FILE__ ) );
define( 'COS_AB_URL', plugin_dir_url( __FILE__ ) );

require_once COS_AB_PATH . 'includes/assign_variant.php';
require_once COS_AB_PATH . 'includes/render_cta.php';

/**
 * Enqueue scripts
 */
function cos_ab_enqueue_scripts() {
    wp_enqueue_script( 'cos-ab-js', COS_AB_URL . 'assets/ab.js', array(), '1.0.0', true );

    $default_api_url = trailingslashit( home_url() ) . 'wp-json/content-os/v1/track/event';
    $configured_api_url = get_option( 'cos_ab_track_api_url', $default_api_url );
    $api_url = apply_filters( 'cos_ab_track_api_url', $configured_api_url );

    // Pass API endpoint to JS
    wp_localize_script( 'cos-ab-js', 'cosAbConfig', array(
        'apiUrl' => esc_url_raw( $api_url ),
        'contentId' => get_the_ID()
    ));
}
add_action( 'wp_enqueue_scripts', 'cos_ab_enqueue_scripts' );

/**
 * Shortcode for A/B CTA
 * Usage: [cos_cta_ab sku="SKU123"]
 */
add_shortcode( 'cos_cta_ab', 'cos_ab_render_cta_shortcode' );
