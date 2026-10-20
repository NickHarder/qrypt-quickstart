/**
 * Copy buttons: each button copies the text of the element its data-copy-target names, and the
 * page's status region says so, for screen readers as well as sighted users.
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
