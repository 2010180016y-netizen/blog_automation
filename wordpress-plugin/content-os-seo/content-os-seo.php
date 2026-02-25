<?php
/**
 * Plugin Name: Content OS SEO
 * Description: Minimal Technical SEO for Content OS. Handles Canonical, OG Tags, and Meta Description without heavy plugins.
 * Version: 1.0.0
 * Author: Content OS Team
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Define Constants
define( 'COS_SEO_PATH', plugin_dir_path( __FILE__ ) );

// Load Includes
require_once COS_SEO_PATH . 'includes/helpers.php';
require_once COS_SEO_PATH . 'includes/meta.php';
require_once COS_SEO_PATH . 'includes/canonical.php';
require_once COS_SEO_PATH . 'includes/og.php';
require_once COS_SEO_PATH . 'includes/indexing.php';
require_once COS_SEO_PATH . 'includes/consent.php';

/**
 * Main SEO Hook
 */
function cos_seo_render_tags() {
    // Priority: Meta -> Canonical -> OG
    cos_seo_render_meta_description();
    cos_seo_render_canonical();
    cos_seo_render_og_tags();
    
    // Optional Hreflang Hook
    do_action('cos_seo_extra_tags');
}
add_action( 'wp_head', 'cos_seo_render_tags', 1 );

// Disable default WP canonical if our plugin is active
remove_action( 'wp_head', 'rel_canonical' );
