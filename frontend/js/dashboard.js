// Dashboard: greeting, today's status and simple weekly stats.

import { apiRequest } from "./api.js";
import { formatDateGerman, logout, requireAuth, todayIso } from "./utils.js";

const MOOD_EMOJIS = { 1: "😢", 2: "😕", 3: "😐", 4: "🙂", 5: "😄" };

function isoDaysAgo(days) {
    const date = new Date();
    date.setDate(date.getDate() - days);
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${date.getFullYear()}-${month}-${day}`;
}

function initWeeklySummary() {
    const button = document.getElementById("weekly-summary-button");
    const output = document.getElementById("weekly-summary");
    button.addEventListener("click", async () => {
        button.disabled = true;
        output.textContent = "Erstelle Zusammenfassung …";
        try {
            const data = await apiRequest("/ai/weekly-summary", { method: "POST" });
            output.textContent = data.summary;
            output.classList.remove("muted");
        } catch {
            output.textContent =
                "Zusammenfassung konnte nicht erstellt werden.";
        } finally {
            button.disabled = false;
        }
    });
}

export async function initDashboard() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);
    initWeeklySummary();
    document.getElementById("today-date").textContent =
        formatDateGerman(todayIso());

    try {
        const user = await apiRequest("/users/me");
        document.getElementById("greeting").textContent =
            `Hallo ${user.username} 👋`;
    } catch {
        logout();
        return;
    }

    // Today's entry (404 simply means: not written yet)
    try {
        const today = await apiRequest("/journal/today");
        if (today.mood_score) {
            document.getElementById("stat-mood").textContent =
                `${MOOD_EMOJIS[today.mood_score]} ${today.mood_score}/5`;
        }
        document.getElementById("today-status").textContent =
            "Du hast heute schon geschrieben ✨";
        document.getElementById("today-link").textContent =
            "Eintrag ansehen oder bearbeiten";
    } catch {
        // no entry yet — keep the default texts
    }

    // Last 7 days
    try {
        const entries = await apiRequest(
            `/journal?start_date=${isoDaysAgo(6)}&end_date=${todayIso()}`
        );
        document.getElementById("stat-week").textContent =
            `${entries.length} von 7 Tagen`;
        const sportDays = entries.filter((e) => e.did_sport).length;
        document.getElementById("stat-sport").textContent =
            `${sportDays} ${sportDays === 1 ? "Tag" : "Tage"}`;
    } catch {
        // stats stay at "–"
    }

    // Streak
    try {
        const streak = await apiRequest("/streak");
        document.getElementById("stat-streak").textContent =
            `🔥 ${streak.current_streak} ${streak.current_streak === 1 ? "Tag" : "Tage"}`;
    } catch {
        // stat stays at "–"
    }

    // Habits today
    try {
        const habits = await apiRequest(`/habits/daily?for_date=${todayIso()}`);
        if (habits.length > 0) {
            const done = habits.filter(
                (h) => h.today_log && h.today_log.completed
            ).length;
            document.getElementById("stat-habits").textContent =
                `${done} von ${habits.length}`;
        } else {
            document.getElementById("stat-habits").textContent = "–";
        }
    } catch {
        // stat stays at "–"
    }
}
