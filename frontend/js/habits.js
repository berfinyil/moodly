// Habits page: daily check-off list and habit creation.

import { apiRequest } from "./api.js";
import { logout, requireAuth, showToast, todayIso } from "./utils.js";

/** Reload the daily habit list and progress line. */
async function renderHabits() {
    const list = document.getElementById("habit-list");
    const progress = document.getElementById("habit-progress");
    const habits = await apiRequest(`/habits/daily?for_date=${todayIso()}`);

    list.innerHTML = "";
    if (habits.length === 0) {
        const empty = document.createElement("li");
        empty.className = "muted";
        empty.textContent =
            "Noch keine Habits – lege unten deinen ersten an. 🌱";
        list.appendChild(empty);
        progress.textContent = "";
        return;
    }

    const doneCount = habits.filter(
        (h) => h.today_log && h.today_log.completed
    ).length;
    progress.textContent =
        `Heute: ${doneCount} von ${habits.length} abgeschlossen`;

    for (const habit of habits) {
        list.appendChild(buildHabitRow(habit));
    }
}

/** One row: checkbox, name, optional value input, delete button. */
function buildHabitRow(habit) {
    const row = document.createElement("li");
    row.className = "habit-row";
    const done = Boolean(habit.today_log && habit.today_log.completed);

    const label = document.createElement("label");
    label.className = "checkbox-label habit-check";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = done;

    const name = document.createElement("span");
    name.textContent = habit.name;
    if (done) name.classList.add("habit-done");

    label.append(checkbox, name);
    row.appendChild(label);

    // Optional numeric value (e.g. minutes) for habits with a target
    let valueInput = null;
    if (habit.target_value !== null) {
        valueInput = document.createElement("input");
        valueInput.type = "number";
        valueInput.min = "0";
        valueInput.className = "habit-value";
        valueInput.placeholder = `Ziel: ${habit.target_value}`;
        if (habit.today_log && habit.today_log.value !== null) {
            valueInput.value = habit.today_log.value;
        }
        const unit = document.createElement("span");
        unit.className = "muted";
        unit.textContent = habit.unit ?? "";
        row.append(valueInput, unit);
    }

    const save = async (completed) => {
        try {
            await apiRequest(`/habits/${habit.id}/logs`, {
                method: "POST",
                body: JSON.stringify({
                    log_date: todayIso(),
                    completed,
                    value:
                        valueInput && valueInput.value !== ""
                            ? Number(valueInput.value)
                            : null,
                }),
            });
            await renderHabits();
        } catch (error) {
            showToast(error.message, "error");
        }
    };

    checkbox.addEventListener("change", () => save(checkbox.checked));
    if (valueInput) {
        valueInput.addEventListener("change", () => save(checkbox.checked));
    }

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "habit-delete";
    remove.title = "Habit löschen";
    remove.textContent = "🗑";
    remove.addEventListener("click", async () => {
        if (!confirm(`Habit „${habit.name}“ wirklich löschen?`)) return;
        try {
            await apiRequest(`/habits/${habit.id}`, { method: "DELETE" });
            showToast("Habit gelöscht.", "success");
            await renderHabits();
        } catch (error) {
            showToast(error.message, "error");
        }
    });
    row.appendChild(remove);

    return row;
}

function initHabitForm() {
    const form = document.getElementById("habit-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await apiRequest("/habits", {
                method: "POST",
                body: JSON.stringify({
                    name: form.name.value.trim(),
                    target_value:
                        form.target_value.value !== ""
                            ? Number(form.target_value.value)
                            : null,
                    unit: form.unit.value.trim() || null,
                }),
            });
            form.reset();
            showToast("Habit angelegt 🌱", "success");
            await renderHabits();
        } catch (error) {
            showToast(error.message, "error");
        }
    });
}

export async function initHabitsPage() {
    requireAuth();
    document.getElementById("logout-button").addEventListener("click", logout);
    initHabitForm();
    try {
        await renderHabits();
    } catch (error) {
        showToast("Habits konnten nicht geladen werden.", "error");
    }
}
