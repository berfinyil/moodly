// Analytics page: renders the charts from the backend's computed numbers.
// All statistics are calculated server-side; this file only displays them.

import { apiRequest } from "./api.js";
import { logout, requireAuth, showToast } from "./utils.js";

// Validated data colors (CVD-checked): green = primary series, blue = contrast
const DATA_GREEN = "#3f8d52";
const DATA_BLUE = "#3573c4";
const GRID_COLOR = "rgba(0, 0, 0, 0.06)";
const TEXT_MUTED = "#7a756e";

const BASE_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
};

function scale(overrides = {}) {
    return {
        grid: { color: GRID_COLOR },
        ticks: { color: TEXT_MUTED },
        border: { display: false },
        ...overrides,
    };
}

function formatShortDate(isoDate) {
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString("de-DE", {
        day: "numeric",
        month: "short",
    });
}

/* ---------- Individual charts ---------- */

async function renderSummary() {
    const data = await apiRequest("/analytics/summary");
    document.getElementById("data-level-hint").textContent = data.data_level_hint;
    document.getElementById("stat-total").textContent = data.total_entries;
    document.getElementById("stat-mood7").textContent =
        data.average_mood_last_7_days !== null
            ? `${data.average_mood_last_7_days.toLocaleString("de-DE")}/5`
            : "–";
    document.getElementById("stat-sport30").textContent = data.sport_days_last_30_days;
}

async function renderMoodChart() {
    const data = await apiRequest("/analytics/mood?days=30");
    new Chart(document.getElementById("mood-chart"), {
        type: "line",
        data: {
            labels: data.points.map((p) => formatShortDate(p.entry_date)),
            datasets: [
                {
                    label: "Stimmung",
                    data: data.points.map((p) => p.mood_score),
                    borderColor: DATA_GREEN,
                    backgroundColor: DATA_GREEN,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.3,
                    spanGaps: true,
                },
            ],
        },
        options: {
            ...BASE_OPTIONS,
            scales: {
                y: { ...scale(), min: 1, max: 5, ticks: { stepSize: 1, color: TEXT_MUTED } },
                x: { ...scale({ grid: { display: false } }), ticks: { color: TEXT_MUTED, maxTicksLimit: 10 } },
            },
        },
    });
}

async function renderWeekdayChart() {
    const data = await apiRequest("/analytics/weekday");
    if (data.weekdays.length === 0) {
        document.getElementById("weekday-hint").textContent =
            "Noch nicht genügend Daten für eine zuverlässige Auswertung.";
        return;
    }
    if (data.best_weekday && data.worst_weekday) {
        document.getElementById("weekday-hint").textContent =
            `In deinen dokumentierten Daten ist die Stimmung am ${data.best_weekday} ` +
            `durchschnittlich am höchsten und am ${data.worst_weekday} am niedrigsten.`;
    }
    new Chart(document.getElementById("weekday-chart"), {
        type: "bar",
        data: {
            labels: data.weekdays.map((w) => w.weekday_name),
            datasets: [
                {
                    label: "Ø Stimmung",
                    data: data.weekdays.map((w) => w.average_mood),
                    backgroundColor: DATA_GREEN,
                    borderRadius: 4,
                    maxBarThickness: 36,
                },
            ],
        },
        options: {
            ...BASE_OPTIONS,
            scales: {
                y: { ...scale(), min: 0, max: 5, ticks: { stepSize: 1, color: TEXT_MUTED } },
                x: scale({ grid: { display: false } }),
            },
        },
    });
}

async function renderSportChart() {
    const data = await apiRequest("/analytics/sport");
    document.getElementById("sport-statement").textContent = data.statement ?? "";
    if (data.average_mood_sport_days === null && data.average_mood_no_sport_days === null) {
        return;
    }
    new Chart(document.getElementById("sport-chart"), {
        type: "bar",
        data: {
            labels: [
                `Sporttage (${data.sport_days})`,
                `Ohne Sport (${data.no_sport_days})`,
            ],
            datasets: [
                {
                    label: "Ø Stimmung",
                    data: [data.average_mood_sport_days, data.average_mood_no_sport_days],
                    backgroundColor: [DATA_GREEN, DATA_BLUE],
                    borderRadius: 4,
                    maxBarThickness: 48,
                },
            ],
        },
        options: {
            ...BASE_OPTIONS,
            indexAxis: "y",
            scales: {
                x: { ...scale(), min: 0, max: 5, ticks: { stepSize: 1, color: TEXT_MUTED } },
                y: scale({ grid: { display: false } }),
            },
        },
    });
}

async function renderHabitChart() {
    const data = await apiRequest("/analytics/habits?days=30");
    if (data.length === 0) return;
    new Chart(document.getElementById("habit-chart"), {
        type: "bar",
        data: {
            labels: data.map((h) => h.habit_name),
            datasets: [
                {
                    label: "Erfolgsquote",
                    data: data.map((h) => Math.round(h.completion_rate * 100)),
                    backgroundColor: DATA_GREEN,
                    borderRadius: 4,
                    maxBarThickness: 36,
                },
            ],
        },
        options: {
            ...BASE_OPTIONS,
            indexAxis: "y",
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: { label: (ctx) => `${ctx.parsed.x} % der letzten 30 Tage` },
                },
            },
            scales: {
                x: { ...scale(), min: 0, max: 100, ticks: { callback: (v) => `${v} %`, color: TEXT_MUTED } },
                y: scale({ grid: { display: false } }),
            },
        },
    });
}

async function renderEmotionChart() {
    const data = await apiRequest("/analytics/emotions?days=30");
    if (data.length === 0) return;
    const top = data.slice(0, 8);
    new Chart(document.getElementById("emotion-chart"), {
        type: "bar",
        data: {
            labels: top.map((e) => `${e.emoji} ${e.name}`),
            datasets: [
                {
                    label: "Anzahl Tage",
                    data: top.map((e) => e.count),
                    backgroundColor: DATA_GREEN,
                    borderRadius: 4,
                    maxBarThickness: 36,
                },
            ],
        },
        options: {
            ...BASE_OPTIONS,
            scales: {
                y: { ...scale(), beginAtZero: true, ticks: { precision: 0, color: TEXT_MUTED } },
                x: scale({ grid: { display: false } }),
            },
        },
    });
}

/* ---------- Init ---------- */

export async function initAnalyticsPage() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);

    const renderers = [
        renderSummary,
        renderMoodChart,
        renderWeekdayChart,
        renderSportChart,
        renderHabitChart,
        renderEmotionChart,
    ];
    for (const render of renderers) {
        try {
            await render();
        } catch (error) {
            showToast("Ein Teil der Analytics konnte nicht geladen werden.", "error");
        }
    }
}
