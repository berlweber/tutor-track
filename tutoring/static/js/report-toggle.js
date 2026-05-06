document.addEventListener("DOMContentLoaded", () => {
  const reportToggles = document.querySelectorAll(".js-report-toggle");

  // toggles the expand state to match the value of 'expanded' through 
  // toggle the 'is-expanded' class according to 'expanded',
  // set the 'aria-expanded' attribute according to 'expanded',
  // and finaly also the see more/see less label according to 'expanded'.
  const setExpandedState = (toggle, expanded) => {
    const label = toggle.querySelector(".report-toggle-label");
    const moreLabel = toggle.dataset.moreLabel || "See more";
    const lessLabel = toggle.dataset.lessLabel || "See less";

    toggle.classList.toggle("is-expanded", expanded);
    toggle.setAttribute("aria-expanded", String(expanded));

    if (label) {
      label.textContent = expanded ? lessLabel : moreLabel;
    }
  };

  reportToggles.forEach((toggle) => {
    // caches the reports actual text in order to exit if there is no text
    const text = toggle.querySelector(".report-toggle-text");
    if (!text) return;
    const updateCell = toggle.closest(".dashboard-update-cell[data-update-url]");

    const syncCellLinkState = (isLinkable) => {
      if (!updateCell) return;

      updateCell.classList.toggle("is-cell-link", isLinkable);
      if (isLinkable) {
        updateCell.setAttribute("role", "link");
        updateCell.setAttribute("tabindex", "0");
      } else {
        updateCell.removeAttribute("role");
        updateCell.removeAttribute("tabindex");
      }
    };

    if (updateCell && !updateCell.dataset.linkHandlerBound) {
      updateCell.dataset.linkHandlerBound = "true";

      const shouldIgnoreCellLink = (event) =>
        event.target.closest("a, button") || event.target.closest(".js-report-toggle.is-collapsible");

      updateCell.addEventListener("click", (event) => {
        if (!updateCell.classList.contains("is-cell-link") || shouldIgnoreCellLink(event)) return;
        window.location.href = updateCell.dataset.updateUrl;
      });

      updateCell.addEventListener("keydown", (event) => {
        if (!updateCell.classList.contains("is-cell-link")) return;
        if (event.key !== "Enter" && event.key !== " ") return;
        if (shouldIgnoreCellLink(event)) return;

        event.preventDefault();
        window.location.href = updateCell.dataset.updateUrl;
      });
    }

    const syncCollapsibleState = () => {
      const wasExpanded = toggle.classList.contains("is-expanded");
      // removes expanded at the begining to test if its collapsible
      if (wasExpanded) {
        toggle.classList.remove("is-expanded");
      }

      // adding a is-collapsible class to toggle element only if its collapsible
      const isCollapsible = text.scrollHeight > text.clientHeight + 1;
      toggle.classList.toggle("is-collapsible", isCollapsible);
      syncCellLinkState(!isCollapsible);

      // returns the expanded class if it was present before
      if (wasExpanded) {
        toggle.classList.add("is-expanded");
      }

      if (isCollapsible) {
        // sets it to be tab-focusable and set to the previous expanded-state
        toggle.setAttribute("role", "button");
        toggle.setAttribute("tabindex", "0");
        setExpandedState(toggle, wasExpanded);
      } else {
        toggle.classList.remove("is-expanded");
        toggle.setAttribute("aria-expanded", "false");
        toggle.removeAttribute("role");
        toggle.removeAttribute("tabindex");
      }
    };

    const toggleExpanded = (event) => {
      if (!toggle.classList.contains("is-collapsible")) return;

      event.preventDefault();
      event.stopPropagation();
      setExpandedState(toggle, !toggle.classList.contains("is-expanded"));
    };

    toggle.addEventListener("click", toggleExpanded);
    toggle.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      toggleExpanded(event);
    });

    syncCollapsibleState();
    window.addEventListener("resize", syncCollapsibleState);
  });
});
