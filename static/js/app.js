document.addEventListener('DOMContentLoaded', () => {
    const progressBars = document.querySelectorAll('.progress-fill');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 120);
    });

    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', event => {
            const message = form.dataset.confirm || 'Are you sure?';
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const dateInputs = document.querySelectorAll('input[type="date"]');

    dateInputs.forEach(function (input) {
        if (input.parentElement.classList.contains("date-field-wrapper")) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "date-field-wrapper";

        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "date-picker-button";
        button.setAttribute("aria-label", "Open calendar");

        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
        `;

        button.addEventListener("click", function () {
            if (typeof input.showPicker === "function") {
                input.showPicker();
            } else {
                input.focus();
                input.click();
            }
        });

        wrapper.appendChild(button);
    });
});
