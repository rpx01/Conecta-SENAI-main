(function () {
    function selectElements() {
        const checkbox = document.getElementById('noticiaCalendario');
        const container = document.getElementById('noticiaDataEventoContainer');
        const input = document.getElementById('noticiaDataEvento');
        return { checkbox, container, input };
    }

    function applyVisibility({ checkbox, container, input }) {
        if (!container) {
            return;
        }
        const shouldShow = Boolean(checkbox && checkbox.checked);
        container.classList.toggle('d-none', !shouldShow);
        container.toggleAttribute('hidden', !shouldShow);
        container.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');
        if (input) {
            input.required = shouldShow;
            if (!shouldShow) {
                input.value = '';
            }
        }
    }

    function setupObservers(elements) {
        if (!elements.checkbox) {
            return;
        }
        const { checkbox } = elements;
        const observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'checked') {
                    applyVisibility(elements);
                }
            }
        });
        observer.observe(checkbox, { attributes: true, attributeFilter: ['checked'] });
    }

    function init() {
        const elements = selectElements();
        if (!elements.checkbox || !elements.container) {
            return;
        }

        const handler = () => applyVisibility(elements);
        elements.checkbox.addEventListener('change', handler);
        elements.checkbox.addEventListener('input', handler);
        setupObservers(elements);
        applyVisibility(elements);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();
