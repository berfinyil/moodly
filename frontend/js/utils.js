// Small shared helpers: toasts, date formatting, auth guard.

/** Show a temporary toast message at the bottom of the screen. */
export function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add("visible"), 10);
    setTimeout(() => {
        toast.classList.remove("visible");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/** Today's date as YYYY-MM-DD in local time. */
export function todayIso() {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${now.getFullYear()}-${month}-${day}`;
}

/** Format YYYY-MM-DD as a readable German date, e.g. "10. August 2026". */
export function formatDateGerman(isoDate) {
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString("de-DE", {
        day: "numeric",
        month: "long",
        year: "numeric",
    });
}

/** Redirect to login if no token is stored. Call at the top of protected pages. */
export function requireAuth() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "login.html";
    }
}

/** Remove the token and go back to the login page. */
export function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}
