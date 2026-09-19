// Achievements page: streaks and the badge grid.

import { apiRequest } from "./api.js";
import { logout, requireAuth, showToast } from "./utils.js";

function formatUnlockDate(isoDatetime) {
    return new Date(isoDatetime).toLocaleDateString("de-DE", {
        day: "numeric",
        month: "long",
        year: "numeric",
    });
}

export async function initAchievementsPage() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);

    try {
        const streak = await apiRequest("/streak");
        document.getElementById("streak-line").textContent =
            `🔥 Aktuelle Streak: ${streak.current_streak} ` +
            `${streak.current_streak === 1 ? "Tag" : "Tage"} · ` +
            `Längste Streak: ${streak.longest_streak} ` +
            `${streak.longest_streak === 1 ? "Tag" : "Tage"}`;
    } catch {
        // streak line stays empty
    }

    try {
        const achievements = await apiRequest("/achievements");
        const grid = document.getElementById("achievement-grid");
        grid.innerHTML = "";
        for (const item of achievements) {
            const card = document.createElement("div");
            const unlocked = item.unlocked_at !== null;
            card.className = `card achievement-card${unlocked ? "" : " locked"}`;

            const emoji = document.createElement("span");
            emoji.className = "achievement-emoji";
            emoji.textContent = unlocked ? item.achievement.emoji : "🔒";

            const name = document.createElement("strong");
            name.textContent = item.achievement.name;

            const description = document.createElement("span");
            description.className = "muted";
            description.textContent = item.achievement.description;

            card.append(emoji, name, description);

            if (unlocked) {
                const when = document.createElement("span");
                when.className = "achievement-date";
                when.textContent =
                    `Freigeschaltet am ${formatUnlockDate(item.unlocked_at)}`;
                card.appendChild(when);
            }
            grid.appendChild(card);
        }
    } catch (error) {
        showToast("Achievements konnten nicht geladen werden.", "error");
    }
}
