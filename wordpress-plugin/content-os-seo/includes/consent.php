<?php
/**
 * Consent banner + Google Consent Mode integration for EEA/UK/CH traffic.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function cos_seo_consent_enabled() {
	$enabled = apply_filters( 'cos_seo_consent_enabled', true );
	return (bool) $enabled;
}

function cos_seo_consent_target_regions() {
	$regions = array(
		'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT',
		'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO',
		'GB', 'UK', 'CH',
	);

	$filtered = apply_filters( 'cos_seo_consent_regions', $regions );
	return is_array( $filtered ) ? array_values( $filtered ) : $regions;
}

function cos_seo_detect_country_code() {
	$keys = array( 'HTTP_CF_IPCOUNTRY', 'GEOIP_COUNTRY_CODE', 'HTTP_X_COUNTRY_CODE' );
	foreach ( $keys as $key ) {
		if ( ! empty( $_SERVER[ $key ] ) ) {
			return strtoupper( sanitize_text_field( wp_unslash( $_SERVER[ $key ] ) ) );
		}
	}
	return '';
}

function cos_seo_region_requires_consent() {
	$country_code = cos_seo_detect_country_code();
	if ( '' === $country_code ) {
		return false;
	}

	return in_array( $country_code, cos_seo_consent_target_regions(), true );
}

function cos_seo_render_consent_mode_defaults() {
	if ( ! cos_seo_consent_enabled() ) {
		return;
	}

	$requires_consent = cos_seo_region_requires_consent();
	$default_state    = $requires_consent ? 'denied' : 'granted';
	$region_json      = wp_json_encode( cos_seo_consent_target_regions() );
	$country_code     = esc_js( cos_seo_detect_country_code() );
	?>
	<script>
	window.dataLayer = window.dataLayer || [];
	function gtag(){dataLayer.push(arguments);} // eslint-disable-line no-unused-vars
	window.COSConsent = window.COSConsent || {
		version: 1,
		requiresConsent: <?php echo $requires_consent ? 'true' : 'false'; ?>,
		countryCode: "<?php echo $country_code; ?>",
		targetRegions: <?php echo $region_json; ?>
	};

	gtag('consent', 'default', {
		'ad_storage': '<?php echo esc_js( $default_state ); ?>',
		'analytics_storage': '<?php echo esc_js( $default_state ); ?>',
		'ad_user_data': '<?php echo esc_js( $default_state ); ?>',
		'ad_personalization': '<?php echo esc_js( $default_state ); ?>',
		'wait_for_update': 500
	});
	</script>
	<?php
}
add_action( 'wp_head', 'cos_seo_render_consent_mode_defaults', 0 );

function cos_seo_render_cmp_banner() {
	if ( ! cos_seo_consent_enabled() || ! cos_seo_region_requires_consent() || is_admin() ) {
		return;
	}
	?>
	<style>
	#cos-consent-banner { position: fixed; left: 16px; right: 16px; bottom: 16px; z-index: 99999; background: #111; color: #fff; padding: 16px; border-radius: 10px; box-shadow: 0 8px 20px rgba(0,0,0,.2); font-size: 14px; }
	#cos-consent-banner p { margin: 0 0 10px 0; line-height: 1.4; }
	#cos-consent-actions { display: flex; gap: 8px; flex-wrap: wrap; }
	#cos-consent-actions button { border: 0; border-radius: 6px; padding: 8px 12px; cursor: pointer; font-weight: 600; }
	#cos-consent-accept { background: #2e7d32; color: #fff; }
	#cos-consent-reject { background: #b71c1c; color: #fff; }
	#cos-consent-manage { background: #eceff1; color: #111; }
	</style>
	<div id="cos-consent-banner" role="dialog" aria-live="polite" aria-label="Cookie consent" hidden>
		<p>
			We use cookies for ads and analytics. You can accept all, reject non-essential usage, or manage later.
		</p>
		<div id="cos-consent-actions">
			<button id="cos-consent-accept" type="button">Accept</button>
			<button id="cos-consent-reject" type="button">Reject</button>
			<button id="cos-consent-manage" type="button">Privacy settings</button>
		</div>
	</div>
	<script>
	(function() {
		var key = 'cos_consent_v1';
		var banner = document.getElementById('cos-consent-banner');
		if (!banner) return;

		function applyConsent(granted) {
			var state = granted ? 'granted' : 'denied';
			if (typeof gtag === 'function') {
				gtag('consent', 'update', {
					'ad_storage': state,
					'analytics_storage': state,
					'ad_user_data': state,
					'ad_personalization': state
				});
			}
			window.dispatchEvent(new CustomEvent('cos_consent_updated', { detail: { granted: !!granted } }));
		}

		function persistConsent(granted) {
			var value = granted ? 'granted' : 'denied';
			localStorage.setItem(key, value);
			document.cookie = key + '=' + value + ';path=/;max-age=' + (60 * 60 * 24 * 180) + ';SameSite=Lax';
		}

		function readConsent() {
			var stored = localStorage.getItem(key);
			if (stored) return stored;
			var match = document.cookie.match(new RegExp('(?:^|; )' + key + '=([^;]*)'));
			return match ? decodeURIComponent(match[1]) : null;
		}

		var initial = readConsent();
		if (initial === 'granted' || initial === 'denied') {
			applyConsent(initial === 'granted');
			return;
		}

		banner.hidden = false;
		document.getElementById('cos-consent-accept').addEventListener('click', function() {
			persistConsent(true);
			applyConsent(true);
			banner.hidden = true;
		});
		document.getElementById('cos-consent-reject').addEventListener('click', function() {
			persistConsent(false);
			applyConsent(false);
			banner.hidden = true;
		});
		document.getElementById('cos-consent-manage').addEventListener('click', function() {
			window.location.href = '/privacy-policy';
		});
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'cos_seo_render_cmp_banner', 99 );
