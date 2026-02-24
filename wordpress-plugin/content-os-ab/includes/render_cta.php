<?php
/**
 * CTA Rendering Logic
 */

function cos_ab_render_cta_shortcode( $atts ) {
    $atts = shortcode_atts( array(
        'sku' => '',
    ), $atts );

    $variant = cos_ab_get_visitor_variant();
    $sku = $atts['sku'];
    
    // Define Variants
    $config = array(
        'A' => array(
            'text' => '지금 바로 구매하기',
            'class' => 'cta-btn-primary',
            'position' => 'bottom'
        ),
        'B' => array(
            'text' => '최저가 확인하고 혜택 받기',
            'class' => 'cta-btn-accent',
            'position' => 'bottom'
        )
    );

    $current = $config[$variant];
    
    ob_start();
    ?>
    <div class="cos-cta-container" data-variant="<?php echo esc_attr($variant); ?>" data-sku="<?php echo esc_attr($sku); ?>">
        <a href="#" class="cos-cta-button <?php echo esc_attr($current['class']); ?>" 
           id="cos-cta-<?php echo esc_attr($sku); ?>"
           data-intent="buy">
            <?php echo esc_html($current['text']); ?>
        </a>
    </div>
    <style>
        .cos-cta-button { padding: 15px 30px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: bold; }
        .cta-btn-primary { background: #007bff; color: #fff; }
        .cta-btn-accent { background: #ff4e00; color: #fff; }
    </style>
    <?php
    return ob_get_clean();
}
