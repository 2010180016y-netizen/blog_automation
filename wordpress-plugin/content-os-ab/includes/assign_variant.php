<?php
/**
 * Variant Assignment Logic
 */

function cos_ab_get_visitor_variant() {
    $cookie_name = 'cos_ab_variant';
    
    if ( isset( $_COOKIE[$cookie_name] ) ) {
        return $_COOKIE[$cookie_name];
    }

    // Assign new variant
    $variant = ( rand( 0, 1 ) === 0 ) ? 'A' : 'B';
    
    // Set cookie for 30 days
    setcookie( $cookie_name, $variant, time() + ( 30 * DAY_IN_SECONDS ), COOKIEPATH, COOKIE_DOMAIN );
    
    return $variant;
}
