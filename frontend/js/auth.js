// Login and registration form handling.

import { apiRequest } from "./api.js";
import { showToast } from "./utils.js";

/** Wire up the login form (login.html). */
export function initLoginPage() {
    const form = document.getElementById("login-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = form.querySelector("button[type=submit]");
        button.disabled = true;
        try {
            const data = await apiRequest("/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: form.email.value.trim(),
                    password: form.password.value,
                }),
            });
            localStorage.setItem("access_token", data.access_token);
            window.location.href = "dashboard.html";
        } catch (error) {
            showToast(error.message, "error");
            button.disabled = false;
        }
    });
}

/** Wire up the registration form (register.html). */
export function initRegisterPage() {
    const form = document.getElementById("register-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = form.querySelector("button[type=submit]");
        button.disabled = true;
        try {
            await apiRequest("/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    email: form.email.value.trim(),
                    username: form.username.value.trim(),
                    password: form.password.value,
                }),
            });
            // Log in right away for a smooth first experience
            const login = await apiRequest("/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: form.email.value.trim(),
                    password: form.password.value,
                }),
            });
            localStorage.setItem("access_token", login.access_token);
            window.location.href = "dashboard.html";
        } catch (error) {
            showToast(error.message, "error");
            button.disabled = false;
        }
    });
}
