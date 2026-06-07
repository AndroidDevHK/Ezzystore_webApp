
// --- SALE RETURN MODAL LOGIC ---

let _currentReturnItems = [];

async function openSaleReturnModal(saleId) {
  document.getElementById('customerHistoryItemsModal')?.classList.remove('show');
  document.getElementById('customerHistoryModal')?.classList.remove('show');
  
  const tbody = document.getElementById("saleReturnBody");
  tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 20px;">Loading sale items...</td></tr>`;
  document.getElementById("saleReturnTitleId").textContent = "#" + saleId;
  document.getElementById("returnSaleId").value = saleId;
  
  document.getElementById("saleReturnModal").classList.add('show');
  
  try {
    const res = await fetch(`/manager/api/sales/${saleId}/items`);
    const data = await res.json();
    if(data.status !== "success") {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger);">${data.error}</td></tr>`;
      return;
    }
    
    document.getElementById("returnCustomerId").value = data.customer_id || "";
    document.getElementById("openSaleReturnConfirm").dataset.originalPending = data.current_balance || 0;
    
    _currentReturnItems = data.items;
    
    if(data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--muted); padding: 20px;">All items have been completely returned.</td></tr>`;
      return;
    }
    
    let html = "";
    data.items.forEach((item, i) => {
      html += `
      <tr data-return-item-id="${item.id}" data-unit-price="${item.unit_price}">
        <td>${i+1}</td>
        <td>${item.product_name} <br> <span class="muted tiny">PKR ${item.unit_price} each</span></td>
        <td>${item.quantity}</td>
        <td>
          <input type="number" class="field return-qty-input" 
            style="width: 70px; margin: 0; padding: 4px;"
            min="1" max="${item.remaining_quantity}" value="${item.remaining_quantity}" disabled>
        </td>
        <td>
          <input type="checkbox" class="return-item-check" onchange="toggleReturnItem(this)">
        </td>
      </tr>`;
    });
    tbody.innerHTML = html;
    calculateReturnButtonState();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger);">Network error fetching items.</td></tr>`;
  }
}

function toggleReturnItem(checkbox) {
  const tr = checkbox.closest('tr');
  const qtyInput = tr.querySelector('.return-qty-input');
  qtyInput.disabled = !checkbox.checked;
  calculateReturnButtonState();
}

function calculateReturnButtonState() {
  const tbody = document.getElementById("saleReturnBody");
  const checked = tbody.querySelectorAll('.return-item-check:checked');
  const btn = document.getElementById("openSaleReturnConfirm");
  btn.disabled = checked.length === 0;
}

document.getElementById("saleReturnBody")?.addEventListener('input', (e) => {
  if(e.target.classList.contains('return-qty-input')) {
    calculateReturnButtonState();
  }
});

document.getElementById("openSaleReturnConfirm")?.addEventListener('click', () => {
  const tbody = document.getElementById("saleReturnBody");
  const checked = tbody.querySelectorAll('.return-item-check:checked');
  let returnValue = 0;
  
  checked.forEach(chk => {
    const tr = chk.closest('tr');
    const price = parseFloat(tr.getAttribute('data-unit-price'));
    const qty = parseInt(tr.querySelector('.return-qty-input').value) || 0;
    returnValue += price * qty;
  });
  
  const originalPending = parseFloat(document.getElementById("openSaleReturnConfirm").dataset.originalPending || 0);
  
  document.getElementById("returnOriginalPending").textContent = "PKR " + originalPending.toFixed(2);
  document.getElementById("returnValueAmount").textContent = "PKR " + returnValue.toFixed(2);
  
  let suggestedPending = originalPending - returnValue;
  let suggestedCash = 0;
  
  if (suggestedPending < 0) {
    suggestedCash = Math.abs(suggestedPending);
    suggestedPending = 0;
  }
  
  document.getElementById("returnRevisedPendingInput").value = suggestedPending.toFixed(0);
  document.getElementById("returnCashRefundedInput").value = suggestedCash.toFixed(0);
  
  document.getElementById('saleReturnModal').classList.remove('show');
  document.getElementById('saleReturnConfirmModal').classList.add('show');
});

document.getElementById("submitSaleReturnBtn")?.addEventListener('click', async () => {
  const btn = document.getElementById("submitSaleReturnBtn");
  btn.disabled = true;
  btn.textContent = "Processing...";
  
  const saleId = document.getElementById("returnSaleId").value;
  const tbody = document.getElementById("saleReturnBody");
  const checked = tbody.querySelectorAll('.return-item-check:checked');
  
  let formData = new FormData();
  formData.append("sale_id", saleId);
  formData.append("revised_pending_amount", document.getElementById("returnRevisedPendingInput").value);
  formData.append("cash_refunded", document.getElementById("returnCashRefundedInput").value);
  
  checked.forEach(chk => {
    const tr = chk.closest('tr');
    const itemId = tr.getAttribute('data-return-item-id');
    const qty = tr.querySelector('.return-qty-input').value;
    formData.append("return_sale_item_id[]", itemId);
    formData.append("return_quantity[]", qty);
  });
  
  try {
    const res = await fetch("/manager/api/sales/return/record", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if(data.status === "success") {
      if(window.showToast) showToast(data.message, "success");
      document.getElementById('saleReturnConfirmModal').classList.remove('show');
      setTimeout(() => location.reload(), 1000); 
    } else {
      if(window.showToast) showToast(data.error, "error");
      btn.disabled = false;
      btn.textContent = "Confirm Return";
    }
  } catch(e) {
    if(window.showToast) showToast("Network error.", "error");
    btn.disabled = false;
    btn.textContent = "Confirm Return";
  }
});
