// Calendar: month view showing which days have entries and their mood.

import { apiRequest } from "./api.js";
import { logout, requireAuth, showToast, todayIso } from "./utils.js";

const MOOD_EMOJIS = { 1: "😢", 2: "😕", 3: "😐", 4: "🙂", 5: "😄" };
const WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];

// Currently shown month
let year;
let month; // 0-11

function isoDate(y, m, day) {
    return `${y}-${String(m + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

async function renderMonth() {
    const heading = document.getElementById("month-heading");
    heading.textContent = new Date(year, month, 1).toLocaleDateString("de-DE", {
        month: "long",
        year: "numeric",
    });

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const startDate = isoDate(year, month, 1);
    const endDate = isoDate(year, month, daysInMonth);

    // date -> mood_score (null = entry without mood)
    let moodByDate = new Map();
    try {
        const days = await apiRequest(
            `/journal/calendar?start_date=${startDate}&end_date=${endDate}`
        );
        moodByDate = new Map(days.map((d) => [d.entry_date, d.mood_score]));
    } catch {
        showToast("Kalender konnte nicht geladen werden.", "error");
    }

    const grid = document.getElementById("calendar-days");
    grid.innerHTML = "";

    // Leading blanks: JS getDay() is 0=Sunday, our week starts Monday
    const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7;
    for (let i = 0; i < firstWeekday; i++) {
        grid.appendChild(document.createElement("div"));
    }

    const today = todayIso();
    for (let day = 1; day <= daysInMonth; day++) {
        const date = isoDate(year, month, day);
        const cell = document.createElement("a");
        cell.className = "calendar-day";
        cell.href = `journal.html?date=${date}`;

        const number = document.createElement("span");
        number.className = "calendar-day-number";
        number.textContent = day;
        cell.appendChild(number);

        if (moodByDate.has(date)) {
            cell.classList.add("has-entry");
            const mood = moodByDate.get(date);
            const emoji = document.createElement("span");
            emoji.className = "calendar-day-mood";
            emoji.textContent = mood !== null ? MOOD_EMOJIS[mood] : "✓";
            cell.appendChild(emoji);
        }
        if (date === today) {
            cell.classList.add("today");
        }
        if (date > today) {
            cell.classList.add("future");
            cell.removeAttribute("href");
        }
        grid.appendChild(cell);
    }
}

export async function initCalendarPage() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);

    const now = new Date();
    year = now.getFullYear();
    month = now.getMonth();

    const weekdayRow = document.getElementById("calendar-weekdays");
    for (const name of WEEKDAYS) {
        const cell = document.createElement("div");
        cell.className = "calendar-weekday";
        cell.textContent = name;
        weekdayRow.appendChild(cell);
    }

    document.getElementById("prev-month").addEventListener("click", () => {
        month -= 1;
        if (month < 0) {
            month = 11;
            year -= 1;
        }
        renderMonth();
    });
    document.getElementById("next-month").addEventListener("click", () => {
        month += 1;
        if (month > 11) {
            month = 0;
            year += 1;
        }
        renderMonth();
    });

    await renderMonth();
}
