/**
 * Client-side A/B tracking
 */
document.addEventListener('DOMContentLoaded', function() {
    const ctaButtons = document.querySelectorAll('.cos-cta-button');
    
    ctaButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const container = this.closest('.cos-cta-container');
            const variant = container.dataset.variant;
            const sku = container.dataset.sku;
            const intent = this.dataset.intent;

            console.log(`CTA Clicked: Variant ${variant}, SKU ${sku}`);

            // Send event to Content OS Tracking API
            if (window.cosAbConfig && window.cosAbConfig.apiUrl) {
                fetch(window.cosAbConfig.apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        event_type: 'cta_click',
                        channel: 'wordpress',
                        content_id: window.cosAbConfig.contentId.toString(),
                        sku: sku,
                        intent: intent,
                        metadata: {
                            variant: variant
                        }
                    })
                }).catch(err => console.error('Tracking failed', err));
            }
        });
    });
});
