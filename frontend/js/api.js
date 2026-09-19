// Central API layer. All backend communication goes through this module.

import { API_BASE_URL } from "./config.js";

/**
 * Send a request to the backend API.
 * Adds the JWT token (once auth exists), handles errors and parses JSON.
 *
 * @param {string} endpoint - e.g. "/health" or "/journal/today"
 * @param {object} options - fetch options (method, body, ...)
 * @returns {Promise<any>} parsed JSON response
 */
export async function apiRequest(endpoint, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    const token = localStorage.getItem("access_token");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    // Expired or invalid session: clear the token and go back to login.
    // Not for /auth/* itself — a failed login should show its error message.
    if (response.status === 401 && !endpoint.startsWith("/auth/")) {
        localStorage.removeItem("access_token");
        window.location.href = "login.html";
        throw new Error("Sitzung abgelaufen. Bitte melde dich neu an.");
    }

    if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
            const errorBody = await response.json();
            message = errorBody.message || errorBody.detail || message;
        } catch {
            // response had no JSON body - keep default message
        }
        throw new Error(message);
    }

    if (response.status === 204) {
        return null;
    }
    return response.json();
}

/** Check whether the backend is reachable. */
export function checkHealth() {
    return apiRequest("/health");
}
