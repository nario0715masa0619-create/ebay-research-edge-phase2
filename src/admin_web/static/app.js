document.addEventListener('DOMContentLoaded', () => {
    // 1. Flash message dismissal
    const dismissButtons = document.querySelectorAll('.flash-dismiss');
    dismissButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const msg = e.target.closest('.flash-message');
            if (msg) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    msg.remove();
                }, 300);
            }
        });
    });

    // 2. Active Context Selector Switchers (Navbar)
    const contextSellers = document.getElementById('context-seller-select');
    const contextEnvs = document.getElementById('context-env-select');

    function updateContextUrl() {
        const url = new URL(window.location.href);
        if (contextSellers) {
            url.searchParams.set('seller_account_id', contextSellers.value);
        }
        if (contextEnvs) {
            url.searchParams.set('environment_type', contextEnvs.value);
        }
        window.location.href = url.toString();
    }

    if (contextSellers) {
        contextSellers.addEventListener('change', updateContextUrl);
    }
    if (contextEnvs) {
        contextEnvs.addEventListener('change', updateContextUrl);
    }

    // 3. Mutation Action Confirmation Guards
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const confirmMsg = form.getAttribute('data-confirm') || 'Are you sure you want to proceed with this operation?';
            const sellerCtx = contextSellers ? contextSellers.value : 'Default';
            const envCtx = contextEnvs ? contextEnvs.value : 'Default';
            
            const isProduction = envCtx.toLowerCase() === 'production';
            let extraWarning = '';
            if (isProduction) {
                extraWarning = '\n\n⚠️ WARNING: THIS IS A PRODUCTION MUTATION! PLEASE DOUBLE CHECK SELLER CONTEXT.';
            }

            const finalConfirm = confirm(`${confirmMsg}\n\n[Active Seller: ${sellerCtx}]\n[Active Environment: ${envCtx}]${extraWarning}`);
            if (!finalConfirm) {
                e.preventDefault();
            }
        });
    });
});
