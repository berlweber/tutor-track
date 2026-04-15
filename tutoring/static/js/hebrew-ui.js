document.addEventListener("DOMContentLoaded", () => {
  const hasFlatpickr = typeof flatpickr !== "undefined";
  const locale = hasFlatpickr && flatpickr.l10ns.he ? flatpickr.l10ns.he : "default";

  if (hasFlatpickr) {
    document.querySelectorAll(".js-he-date").forEach((input) => {
      flatpickr(input, {
        locale,
        dateFormat: "d/m/Y",
        allowInput: true,
        disableMobile: true,
      });
    });

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

    document.querySelectorAll(".js-he-month").forEach((input) => {
      flatpickr(input, {
        locale,
        dateFormat: "Y-m",
        altInput: true,
        altFormat: "F Y",
        allowInput: false,
        disableMobile: true,
        plugins: [
          new monthSelectPlugin({
            shorthand: false,
            dateFormat: "Y-m",
            altFormat: "F Y",
            theme: "light",
          }),
        ],
      });
    });
  }

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
});

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
