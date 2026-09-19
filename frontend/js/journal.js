// Today's journal form: load catalog + existing entry, collect and save.

import { apiRequest } from "./api.js";
import {
    formatDateGerman,
    logout,
    requireAuth,
    showToast,
    todayIso,
} from "./utils.js";

// Page state
let selectedMood = null;
let selectedEmotions = new Map(); // emotion_id -> intensity
let existingEntryId = null;

// The date being edited. Later the calendar can link here with ?date=...
const params = new URLSearchParams(window.location.search);
const entryDate = params.get("date") || todayIso();

function form() {
    return document.getElementById("journal-form");
}

/* ---------- Mood picker ---------- */

function renderMoodSelection() {
    document.querySelectorAll("#mood-picker button").forEach((button) => {
        button.classList.toggle(
            "selected",
            Number(button.dataset.mood) === selectedMood
        );
    });
}

function initMoodPicker() {
    document.querySelectorAll("#mood-picker button").forEach((button) => {
        button.addEventListener("click", () => {
            const mood = Number(button.dataset.mood);
            selectedMood = selectedMood === mood ? null : mood;
            renderMoodSelection();
        });
    });
}

/* ---------- Emotion chips ---------- */

async function initEmotionChips() {
    const container = document.getElementById("emotion-chips");
    const emotions = await apiRequest("/emotions");
    container.innerHTML = "";
    for (const emotion of emotions) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.dataset.emotionId = emotion.id;
        chip.textContent = `${emotion.emoji} ${emotion.name}`;
        chip.addEventListener("click", () => {
            if (selectedEmotions.has(emotion.id)) {
                selectedEmotions.delete(emotion.id);
                chip.classList.remove("selected");
            } else {
                selectedEmotions.set(emotion.id, 3); // default intensity
                chip.classList.add("selected");
            }
        });
        container.appendChild(chip);
    }
}

function renderEmotionSelection() {
    document.querySelectorAll("#emotion-chips .chip").forEach((chip) => {
        chip.classList.toggle(
            "selected",
            selectedEmotions.has(Number(chip.dataset.emotionId))
        );
    });
}

/* ---------- Conditional sections & slider outputs ---------- */

function bindToggles() {
    const f = form();
    const sync = () => {
        document
            .getElementById("sport-details")
            .classList.toggle("hidden", !f.did_sport.checked);
        document
            .getElementById("pain-details")
            .classList.toggle("hidden", !f.had_pain.checked);
    };
    f.did_sport.addEventListener("change", sync);
    f.had_pain.addEventListener("change", sync);
    sync();

    for (const [input, output] of [
        ["energy_level", "energy-output"],
        ["stress_level", "stress-output"],
        ["sleep_quality", "sleep-output"],
        ["pain_level", "pain-output"],
    ]) {
        const el = f[input];
        const out = document.getElementById(output);
        const update = () => (out.textContent = el.value);
        el.addEventListener("input", update);
        update();
    }
}

/* ---------- Load & fill ---------- */

function fillForm(entry) {
    const f = form();
    existingEntryId = entry.id;
    selectedMood = entry.mood_score;
    renderMoodSelection();

    for (const name of ["energy_level", "stress_level", "sleep_quality"]) {
        if (entry[name] !== null) f[name].value = entry[name];
    }
    for (const name of ["did_sport", "had_sex", "cried", "had_headache", "had_pain"]) {
        f[name].checked = entry[name];
    }
    if (entry.pain_level !== null) f.pain_level.value = entry.pain_level;
    for (const name of [
        "mood_influence", "sport_type", "sport_duration_minutes", "pain_location",
        "notes", "gratitude", "positive_event", "negative_event", "reflection",
    ]) {
        f[name].value = entry[name] ?? "";
    }

    selectedEmotions = new Map(
        entry.emotions.map((e) => [e.emotion_id, e.intensity])
    );
    renderEmotionSelection();

    // Re-sync sliders and conditional sections with the loaded values
    bindToggles();
}

/* ---------- Collect & save ---------- */

function collectPayload() {
    const f = form();
    const text = (name) => f[name].value.trim() || null;
    return {
        entry_date: entryDate,
        mood_score: selectedMood,
        energy_level: Number(f.energy_level.value),
        stress_level: Number(f.stress_level.value),
        sleep_quality: Number(f.sleep_quality.value),
        mood_influence: text("mood_influence"),
        did_sport: f.did_sport.checked,
        sport_type: f.did_sport.checked ? text("sport_type") : null,
        sport_duration_minutes:
            f.did_sport.checked && f.sport_duration_minutes.value !== ""
                ? Number(f.sport_duration_minutes.value)
                : null,
        had_sex: f.had_sex.checked,
        cried: f.cried.checked,
        had_headache: f.had_headache.checked,
        had_pain: f.had_pain.checked,
        pain_level: f.had_pain.checked ? Number(f.pain_level.value) : null,
        pain_location: f.had_pain.checked ? text("pain_location") : null,
        notes: text("notes"),
        gratitude: text("gratitude"),
        positive_event: text("positive_event"),
        negative_event: text("negative_event"),
        reflection: text("reflection"),
        emotions: [...selectedEmotions].map(([emotion_id, intensity]) => ({
            emotion_id,
            intensity,
        })),
    };
}

async function saveEntry(event) {
    event.preventDefault();
    const button = form().querySelector("button[type=submit]");
    button.disabled = true;
    try {
        const payload = collectPayload();
        const saved = existingEntryId
            ? await apiRequest(`/journal/${existingEntryId}`, {
                  method: "PUT",
                  body: JSON.stringify(payload),
              })
            : await apiRequest("/journal", {
                  method: "POST",
                  body: JSON.stringify(payload),
              });
        existingEntryId = saved.id;
        document.getElementById("save-status").textContent =
            `Gespeichert um ${new Date().toLocaleTimeString("de-DE")}`;
        showToast("Eintrag gespeichert ✨", "success");
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        button.disabled = false;
    }
}

/* ---------- Init ---------- */

export async function initJournalPage() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);
    document.getElementById("entry-date-heading").textContent =
        formatDateGerman(entryDate);

    initMoodPicker();
    bindToggles();
    form().addEventListener("submit", saveEntry);

    // Daily reflection question (non-critical — ignore failures)
    try {
        const data = await apiRequest("/ai/daily-question");
        document.getElementById("daily-question").textContent =
            `💭 Frage des Tages: ${data.question}`;
    } catch {
        // question stays hidden
    }

    try {
        await initEmotionChips();
    } catch (error) {
        showToast("Emotionen konnten nicht geladen werden.", "error");
    }

    try {
        const entry = await apiRequest(`/journal/date/${entryDate}`);
        fillForm(entry);
    } catch {
        // 404 = no entry for this date yet — start with an empty form
    }
}
