document.addEventListener("DOMContentLoaded", () => {
  const navLinks = Array.from(document.querySelectorAll(".js-assignment-nav-link"));
  const sections = Array.from(document.querySelectorAll("[data-nav-section]"));

  if (!navLinks.length || !sections.length) return;

  const linksById = new Map(
    navLinks
      .map((link) => [decodeURIComponent(link.hash.replace("#", "")), link])
      .filter(([id]) => id)
  );

  const setActiveLink = (sectionId) => {
    const activeLink = linksById.get(sectionId);
    if (!activeLink) return;

    navLinks.forEach((link) => {
      const isActive = link === activeLink;
      link.classList.toggle("is-active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "location");
        link.scrollIntoView({ block: "nearest", inline: "nearest" });
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const sectionId = decodeURIComponent(link.hash.replace("#", ""));
      setActiveLink(sectionId);
    });
  });

  if (!("IntersectionObserver" in window)) {
    const initialId = decodeURIComponent(window.location.hash.replace("#", ""));
    setActiveLink(initialId || sections[0].id);
    return;
  }

  const visibleSections = new Map();
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          visibleSections.set(entry.target.id, entry.intersectionRatio);
        } else {
          visibleSections.delete(entry.target.id);
        }
      });

      if (!visibleSections.size) return;

      const [mostVisibleId] = Array.from(visibleSections.entries()).sort((a, b) => b[1] - a[1])[0];
      setActiveLink(mostVisibleId);
    },
    {
      rootMargin: "-28% 0px -58% 0px",
      threshold: [0.05, 0.2, 0.4, 0.6, 0.8],
    }
  );

  sections.forEach((section) => observer.observe(section));

  const initialId = decodeURIComponent(window.location.hash.replace("#", ""));
  if (initialId) {
    setActiveLink(initialId);
  }
});
