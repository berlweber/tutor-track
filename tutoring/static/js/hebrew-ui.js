const HEBREW_MONTHS = [
  "ינואר",
  "פברואר",
  "מרץ",
  "אפריל",
  "מאי",
  "יוני",
  "יולי",
  "אוגוסט",
  "ספטמבר",
  "אוקטובר",
  "נובמבר",
  "דצמבר",
];

const HEBREW_WEEKDAYS = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];
const customPickerStates = [];

document.addEventListener("DOMContentLoaded", () => {
  initCustomDatePickers();
  initCustomMonthPickers();
  initFlatpickrTimePickers();
  initAutoSubmitMonthForms();
  initValidationMessages();
});

document.addEventListener("click", (event) => {
  customPickerStates.forEach((state) => {
    if (!state.wrapper.contains(event.target)) {
      closeCustomPicker(state);
    }
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") {
    return;
  }

  customPickerStates.forEach((state) => {
    if (state.isOpen) {
      closeCustomPicker(state);
    }
  });
});

function initCustomDatePickers() {
  document.querySelectorAll(".js-he-date").forEach((input) => {
    if (input.dataset.customPickerReady === "true") {
      return;
    }

    const selectedDate = parseDateValue(input.value);
    const state = createCustomPickerState({
      input,
      kind: "date",
      selectedDate,
      viewDate: getMonthStart(selectedDate || new Date()),
    });

    mountCustomPicker(state);
  });
}

function initCustomMonthPickers() {
  document.querySelectorAll(".js-he-month").forEach((input) => {
    if (input.dataset.customPickerReady === "true") {
      return;
    }

    const selectedMonth = parseMonthValue(input.value);
    const state = createCustomPickerState({
      input,
      kind: "month",
      selectedDate: selectedMonth,
      viewDate: getMonthStart(selectedMonth || new Date()),
    });

    mountCustomPicker(state);
  });
}

function initFlatpickrTimePickers() {
  if (typeof flatpickr === "undefined") {
    return;
  }

  const locale = flatpickr.l10ns.he ? flatpickr.l10ns.he : "default";

  document.querySelectorAll(".js-he-clock-time").forEach((input) => {
    flatpickr(input, {
      locale,
      enableTime: true,
      noCalendar: true,
      dateFormat: "H:i",
      time_24hr: true,
      minuteIncrement: 5,
      allowInput: true,
      disableMobile: true,
    });
  });

  document.querySelectorAll(".js-he-duration").forEach((input) => {
    flatpickr(input, {
      locale,
      enableTime: true,
      noCalendar: true,
      dateFormat: "H:i",
      time_24hr: true,
      minuteIncrement: 5,
      allowInput: true,
      disableMobile: true,
      defaultHour: 1,
      defaultMinute: 0,
    });
  });
}

function initValidationMessages() {
  document.querySelectorAll("form").forEach((form) => {
    form.querySelectorAll("input, select, textarea").forEach((field) => {
      field.addEventListener("invalid", () => {
        field.setCustomValidity(getHebrewValidationMessage(field));
      });

      field.addEventListener("input", () => {
        field.setCustomValidity("");
      });

      field.addEventListener("change", () => {
        field.setCustomValidity("");
      });
    });
  });
}

function initAutoSubmitMonthForms() {
  document.querySelectorAll(".js-auto-submit-on-month-change").forEach((form) => {
    const monthInput = form.querySelector(".js-he-month");
    if (!monthInput) {
      return;
    }

    monthInput.addEventListener("change", () => {
      if (monthInput.value) {
        form.requestSubmit();
      }
    });
  });
}

function createCustomPickerState({ input, kind, selectedDate, viewDate }) {
  return {
    input,
    kind,
    selectedDate,
    viewDate,
    panel: null,
    wrapper: null,
    isOpen: false,
  };
}

function mountCustomPicker(state) {
  const wrapper = state.input.closest("p") || state.input.parentElement;
  if (!wrapper) {
    return;
  }

  state.input.dataset.customPickerReady = "true";
  state.input.readOnly = true;
  state.input.classList.add("custom-picker-input");
  state.input.setAttribute("aria-haspopup", "dialog");
  state.input.setAttribute("autocomplete", "off");

  wrapper.classList.add("picker-field");

  const panel = document.createElement("div");
  panel.className = `custom-picker-panel custom-picker-panel--${state.kind}`;
  panel.hidden = true;
  wrapper.appendChild(panel);

  state.panel = panel;
  state.wrapper = wrapper;
  customPickerStates.push(state);

  renderCustomPicker(state);

  state.input.addEventListener("focus", () => {
    openCustomPicker(state);
  });

  state.input.addEventListener("click", (event) => {
    event.preventDefault();
    openCustomPicker(state);
  });

  state.input.addEventListener("keydown", (event) => {
    if (["Enter", " ", "ArrowDown"].includes(event.key)) {
      event.preventDefault();
      openCustomPicker(state);
    }
  });

  panel.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

function openCustomPicker(targetState) {
  customPickerStates.forEach((state) => {
    if (state !== targetState) {
      closeCustomPicker(state);
    }
  });

  renderCustomPicker(targetState);
  targetState.panel.hidden = false;
  targetState.wrapper.classList.add("is-picker-open");
  targetState.input.setAttribute("aria-expanded", "true");
  targetState.isOpen = true;
}

function closeCustomPicker(state) {
  if (!state.panel) {
    return;
  }

  state.panel.hidden = true;
  state.wrapper.classList.remove("is-picker-open");
  state.input.setAttribute("aria-expanded", "false");
  state.isOpen = false;
}

function renderCustomPicker(state) {
  if (!state.panel) {
    return;
  }

  state.panel.innerHTML = state.kind === "date"
    ? buildDatePickerMarkup(state)
    : buildMonthPickerMarkup(state);

  bindCustomPickerEvents(state);
}

function buildDatePickerMarkup(state) {
  const year = state.viewDate.getFullYear();
  const month = state.viewDate.getMonth();
  const firstDayIndex = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = getMonthStart(new Date());
  const selectedKey = state.selectedDate ? toDateKey(state.selectedDate) : "";

  let cells = "";

  for (let index = 0; index < firstDayIndex; index += 1) {
    cells += '<span class="custom-picker-spacer" aria-hidden="true"></span>';
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const currentDate = new Date(year, month, day);
    const isToday =
      currentDate.getFullYear() === today.getFullYear() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getDate() === new Date().getDate();
    const isSelected = toDateKey(currentDate) === selectedKey;

    cells += `
      <button
        type="button"
        class="custom-picker-cell custom-picker-day${isSelected ? " is-selected" : ""}${isToday ? " is-today" : ""}"
        data-date="${toDateKey(currentDate)}"
      >
        ${day}
      </button>
    `;
  }

  return `
    <div class="custom-picker-shell">
      <div class="custom-picker-toolbar">
        <button type="button" class="custom-picker-nav" data-nav="prev-month" aria-label="החודש הקודם">‹</button>
        <div class="custom-picker-title">${HEBREW_MONTHS[month]} ${year}</div>
        <button type="button" class="custom-picker-nav" data-nav="next-month" aria-label="החודש הבא">›</button>
      </div>
      <div class="custom-picker-weekdays">
        ${HEBREW_WEEKDAYS.map((label) => `<span>${label}</span>`).join("")}
      </div>
      <div class="custom-picker-grid custom-picker-grid--days">
        ${cells}
      </div>
    </div>
  `;
}

function buildMonthPickerMarkup(state) {
  const selectedYear = state.selectedDate ? state.selectedDate.getFullYear() : null;
  const selectedMonth = state.selectedDate ? state.selectedDate.getMonth() : null;
  const viewYear = state.viewDate.getFullYear();
  const now = new Date();

  const monthButtons = HEBREW_MONTHS.map((label, index) => {
    const isSelected = selectedYear === viewYear && selectedMonth === index;
    const isToday = now.getFullYear() === viewYear && now.getMonth() === index;

    return `
      <button
        type="button"
        class="custom-picker-cell custom-picker-month${isSelected ? " is-selected" : ""}${isToday ? " is-today" : ""}"
        data-month-index="${index}"
      >
        ${label}
      </button>
    `;
  }).join("");

  return `
    <div class="custom-picker-shell">
      <div class="custom-picker-toolbar">
        <button type="button" class="custom-picker-nav" data-nav="prev-year" aria-label="השנה הקודמת">‹</button>
        <div class="custom-picker-title">${viewYear}</div>
        <button type="button" class="custom-picker-nav" data-nav="next-year" aria-label="השנה הבאה">›</button>
      </div>
      <div class="custom-picker-grid custom-picker-grid--months">
        ${monthButtons}
      </div>
    </div>
  `;
}

function bindCustomPickerEvents(state) {
  if (!state.panel) {
    return;
  }

  state.panel.querySelectorAll("[data-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.nav;
      if (action === "prev-month") {
        state.viewDate = new Date(state.viewDate.getFullYear(), state.viewDate.getMonth() - 1, 1);
      } else if (action === "next-month") {
        state.viewDate = new Date(state.viewDate.getFullYear(), state.viewDate.getMonth() + 1, 1);
      } else if (action === "prev-year") {
        state.viewDate = new Date(state.viewDate.getFullYear() - 1, 0, 1);
      } else if (action === "next-year") {
        state.viewDate = new Date(state.viewDate.getFullYear() + 1, 0, 1);
      }

      renderCustomPicker(state);
    });
  });

  state.panel.querySelectorAll("[data-date]").forEach((button) => {
    button.addEventListener("click", () => {
      const selectedDate = parseIsoDate(button.dataset.date);
      if (!selectedDate) {
        return;
      }

      state.selectedDate = selectedDate;
      state.viewDate = getMonthStart(selectedDate);
      updateInputValue(state.input, formatDateValue(selectedDate));
      closeCustomPicker(state);
    });
  });

  state.panel.querySelectorAll("[data-month-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const monthIndex = Number(button.dataset.monthIndex);
      const selectedMonth = new Date(state.viewDate.getFullYear(), monthIndex, 1);

      state.selectedDate = selectedMonth;
      state.viewDate = getMonthStart(selectedMonth);
      updateInputValue(state.input, formatMonthValue(selectedMonth));
      closeCustomPicker(state);
    });
  });
}

function updateInputValue(input, value) {
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function parseDateValue(value) {
  if (!value) {
    return null;
  }

  const trimmedValue = value.trim();
  let match = trimmedValue.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (match) {
    return createSafeDate(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
  }

  match = trimmedValue.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (match) {
    return createSafeDate(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }

  return null;
}

function parseMonthValue(value) {
  if (!value) {
    return null;
  }

  const trimmedValue = value.trim();
  let match = trimmedValue.match(/^(\d{4})-(\d{2})$/);
  if (match) {
    return createSafeDate(Number(match[1]), Number(match[2]) - 1, 1);
  }

  match = trimmedValue.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (match) {
    return createSafeDate(Number(match[3]), Number(match[2]) - 1, 1);
  }

  match = trimmedValue.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (match) {
    return createSafeDate(Number(match[1]), Number(match[2]) - 1, 1);
  }

  return null;
}

function parseIsoDate(value) {
  if (!value) {
    return null;
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    return null;
  }

  return createSafeDate(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

function createSafeDate(year, monthIndex, day) {
  const date = new Date(year, monthIndex, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== monthIndex ||
    date.getDate() !== day
  ) {
    return null;
  }
  return date;
}

function getMonthStart(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function toDateKey(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function formatDateValue(date) {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${day}/${month}/${date.getFullYear()}`;
}

function formatMonthValue(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${date.getFullYear()}-${month}`;
}

function getHebrewValidationMessage(field) {
  const { validity, tagName, dataset } = field;

  if (validity.valueMissing) {
    if (tagName === "SELECT") {
      return "נא לבחור ערך מהרשימה.";
    }
    if (dataset.pickerType === "date") {
      return "נא לבחור תאריך.";
    }
    if (dataset.pickerType === "month") {
      return "נא לבחור חודש.";
    }
    if (dataset.pickerType === "time") {
      return "נא לבחור שעה.";
    }
    return "נא למלא שדה זה.";
  }

  if (validity.typeMismatch || validity.patternMismatch || validity.badInput) {
    if (dataset.pickerType === "date") {
      return "נא להזין תאריך בפורמט יום/חודש/שנה.";
    }
    if (dataset.pickerType === "month") {
      return "נא לבחור חודש תקין.";
    }
    if (dataset.pickerType === "time") {
      return "נא להזין שעה בפורמט 24 שעות, לדוגמה 18:30.";
    }
    if (dataset.pickerType === "duration") {
      return "נא להזין משך בפורמט שעות:דקות, לדוגמה 01:30.";
    }
    return "הערך שהוזן אינו תקין.";
  }

  if (validity.rangeOverflow || validity.rangeUnderflow || validity.stepMismatch) {
    return "הערך שהוזן אינו בטווח המותר.";
  }

  return "יש לתקן את השדה הזה.";
}
