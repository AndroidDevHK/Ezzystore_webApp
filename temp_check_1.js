
function showCustomerHistoryItems(btn) {
  const itemsJson = btn.getAttribute("data-items");
  if(!itemsJson) return;
  const items = JSON.parse(itemsJson);
  const listEl = document.getElementById("customerHistoryItemsList");
  listEl.innerHTML = "";
  items.forEach(item => {
    const li = document.createElement("li");
    li.style.cssText = "display: flex; justify-content: space-between; padding: 8px 12px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;";
    li.innerHTML = `<span style="font-weight: 600;">${item.name}</span> <span style="color: var(--accent); font-weight: 700;">x${item.quantity}</span>`;
    listEl.appendChild(li);
  });
  document.getElementById("customerHistoryItemsModal").classList.add("show");
}
