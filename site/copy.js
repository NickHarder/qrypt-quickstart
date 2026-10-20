/**
 * The page's two behaviors, both working by keyboard as well as by mouse.
 *
 * Copy buttons: each copies the text of the element its data-copy-target names, and the section's
 * status region says so, for screen readers as well as sighted users.
 *
 * Language tabs (the ARIA tabs pattern): a click, or the arrow, Home and End keys, selects a tab
 * and shows its panel. Without JavaScript every panel stays visible, so the page still works.
 */
for (const copyButton of document.querySelectorAll("button[data-copy-target]")) {
  copyButton.addEventListener("click", async () => {
    const copiedElement = document.getElementById(copyButton.dataset.copyTarget);
    const statusRegion = copyButton.closest("section")?.querySelector(".copy-status");
    try {
      await navigator.clipboard.writeText(copiedElement?.textContent ?? "");
      if (statusRegion) statusRegion.textContent = "Copied to the clipboard.";
    } catch {
      if (statusRegion) statusRegion.textContent = "Could not copy: select the code and copy it.";
    }
  });
}

for (const tabList of document.querySelectorAll('[role="tablist"]')) {
  const tabs = [...tabList.querySelectorAll('[role="tab"]')];
  const selectTab = (selectedTab) => {
    for (const tab of tabs) {
      const isSelected = tab === selectedTab;
      tab.setAttribute("aria-selected", String(isSelected));
      tab.tabIndex = isSelected ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !isSelected;
    }
  };
  tabList.addEventListener("click", (event) => {
    const clickedTab = event.target.closest('[role="tab"]');
    if (clickedTab) selectTab(clickedTab);
  });
  tabList.addEventListener("keydown", (event) => {
    const currentIndex = tabs.indexOf(document.activeElement);
    const nextIndexByKey = {
      ArrowRight: (currentIndex + 1) % tabs.length,
      ArrowLeft: (currentIndex - 1 + tabs.length) % tabs.length,
      Home: 0,
      End: tabs.length - 1,
    };
    const nextIndex = nextIndexByKey[event.key];
    if (nextIndex === undefined || currentIndex === -1) return;
    event.preventDefault();
    selectTab(tabs[nextIndex]);
    tabs[nextIndex].focus();
  });
  selectTab(tabs.find((tab) => tab.getAttribute("aria-selected") === "true") ?? tabs[0]);
}
