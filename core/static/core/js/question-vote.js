for (const form of document.querySelectorAll(
    '[data-question-vote], [data-answer-vote]'
)) {
    const buttons = [...form.querySelectorAll('button[name="value"]')];
    const rating = form.querySelector('[data-vote-rating]');
    const errorBox = form.querySelector('[data-vote-error]');

    let busy = false;

    form.addEventListener('submit', async event => {
        event.preventDefault();

        if (
            busy ||
            !event.submitter ||
            event.submitter.disabled
        ) {
            return;
        }

        const payload = new URLSearchParams(new FormData(form));
        payload.set("value", event.submitter.value);

        const csrfToken = form.elements
            .namedItem("csrfmiddlewaretoken")
            ?.value;

        busy = true;
        errorBox.textContent = "";

        buttons.forEach(button => {
            button.disabled = true;
        });

        try {
            const response = await fetch(form.action, {
                method: "POST",
                mode: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "X-CSRFToken": csrfToken || "",
                },
                body: payload,
            });

            const isJson = response.headers
                .get("Content-Type")
                ?.includes("application/json");

            if (!isJson) {
                errorBox.textContent = response.status === 403
                    ? "Could not verify this request. Refresh the page and try again."
                    : "Could not vote. Please try again.";

                return;
            }

            const data = await response.json();

            if (response.ok || response.status === 409) {
                rating.textContent = data.rating;

                buttons.forEach(button => {
                    const selected = Number(button.value) === data.value;

                    button.setAttribute(
                        "aria-pressed",
                        String(selected)
                    );

                    button.title = selected
                        ? "You already selected this vote"
                        : "";
                });

            }

            if (!response.ok) {
                errorBox.textContent =
                    data.error || "Could not vote. Please try again.";
            }
        } catch {
            errorBox.textContent =
                "Could not vote. Check your connection and try again.";
        } finally {
            busy = false;

            buttons.forEach(button => {
                button.disabled = button.getAttribute("aria-pressed") === "true";
            });

        }
    });
}
