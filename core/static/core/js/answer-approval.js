const approvalForms = [
    ...document.querySelectorAll("[data-answer-approval]")
];

let approvalBusy = false;

for (const form of approvalForms) {
    const checkbox = form.querySelector("[data-approval-checkbox]");
    const errorBox = form.querySelector("[data-approval-error]");

    checkbox.addEventListener("change", async () => {
        const desired = checkbox.checked;

        checkbox.checked = checkbox.defaultChecked;

        if (approvalBusy) {
            return;
        }

        approvalBusy = true;

        for (const other of approvalForms) {
            other.querySelector(
                "[data-approval-checkbox]"
            ).disabled = true;

            other.querySelector(
                "[data-approval-error]"
            ).textContent = "";
        }

        try {
            const response = await fetch(form.action, {
                method: "POST",
                mode: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "X-CSRFToken": form.elements
                        .namedItem("csrfmiddlewaretoken")
                        .value,
                },
                body: new URLSearchParams({
                    question_id: form.elements
                        .namedItem("question_id")
                        .value,

                    answer_id: form.elements
                        .namedItem("answer_id")
                        .value,

                    approved: desired ? "1" : "0",
                }),
            });

            const contentType = response.headers.get("Content-Type") || "";

            if (!contentType.includes("application/json")) {
                errorBox.textContent =
                    "Could not change approval. Please try again.";

                return;
            }

            const data = await response.json();

            if (response.ok) {
                for (const other of approvalForms) {
                    const box = other.querySelector(
                        "[data-approval-checkbox]"
                    );

                    const answerId = other.elements
                        .namedItem("answer_id")
                        .value;

                    const checked =
                        answerId === data.approved_answer_id;

                    box.defaultChecked = checked;
                    box.checked = checked;
                }
            } else {
                errorBox.textContent =
                    data.error || "Could not change approval.";
            }
        } catch {
            errorBox.textContent =
                "Could not change approval. Please try again.";
        } finally {
            approvalBusy = false;

            for (const other of approvalForms) {
                const box = other.querySelector(
                    "[data-approval-checkbox]"
                );

                box.disabled = false;
            }
        }
    });
}
