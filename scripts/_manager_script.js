

  const params = new URLSearchParams(window.location.search);
  if(params.has("sales_report_start") || params.has("sales_report_end")){
    const reportSection = document.getElementById("salesReportSection");
    reportSection?.scrollIntoView({behavior:"smooth", block:"start"});
  }



  const categorySearch = document.getElementById("categorySearch");

  const categoryCards = document.querySelectorAll("[data-category-name]");

  const categoryEmpty = document.getElementById("categoryEmpty");



  if(categorySearch && categoryCards.length){

    // Ensure all category cards are visible on initial load and empty state is hidden
    categoryCards.forEach(card=>{
      card.classList.remove("hidden");
    });
    if(categoryEmpty){
      categoryEmpty.hidden = true;
    }

    const filter = ()=>{

      const term = categorySearch.value.trim().toLowerCase();

      let visible = 0;

      categoryCards.forEach(card=>{

        const match = !term || card.dataset.categoryName.includes(term);

        card.classList.toggle("hidden", !match);

        if(match) visible += 1;

      });

      if(categoryEmpty){

        // Only show empty state if there's a search term and no results
        categoryEmpty.hidden = (visible !== 0) || !term;

      }

    };

    categorySearch.addEventListener("input", filter);

  } else if(categoryEmpty){
    // If no category search or cards, ensure empty state is hidden
    categoryEmpty.hidden = true;
  }

  const categoryManageSearch = document.getElementById("categoryManageSearch");
  const categoryCardGrid = document.getElementById("categoryCardGrid");
  const categoryManageCards = categoryCardGrid ? categoryCardGrid.querySelectorAll(".category-card") : [];
  const categoryManageEmpty = document.getElementById("categoryManageEmpty");

  if(categoryManageSearch && categoryManageCards.length){

    // Ensure all category cards are visible on initial load and empty state is hidden
    categoryManageCards.forEach(card=>{
      card.classList.remove("hidden");
    });
    if(categoryManageEmpty){
      categoryManageEmpty.hidden = true;
    }

    const filterManageCategories = ()=>{

      const term = categoryManageSearch.value.trim().toLowerCase();

      let visible = 0;

      categoryManageCards.forEach(card=>{

        const match = !term || (card.dataset.categoryName || "").includes(term);

        card.classList.toggle("hidden", !match);

        if(match){

          visible += 1;

        }

      });

      if(categoryManageEmpty){

        // Only show empty state if there's a search term and no results
        categoryManageEmpty.hidden = (visible !== 0) || !term;

      }

    };

    categoryManageSearch.addEventListener("input", filterManageCategories);
    // Initialize state on load so the empty state stays hidden until a search is made
    filterManageCategories();

  } else if(categoryManageEmpty){
    // If no category manage search or cards, ensure empty state is hidden
    categoryManageEmpty.hidden = true;
  }



  const brandSearch = document.getElementById("brandSearch");

  const brandCards = document.querySelectorAll("[data-brand-name]");

  const brandEmpty = document.getElementById("brandEmpty");

  if(brandSearch && brandCards.length){

    // Ensure all brand cards are visible on initial load and empty state is hidden
    brandCards.forEach(card=>{
      card.classList.remove("hidden");
    });
    if(brandEmpty){
      brandEmpty.hidden = true;
    }

    const filterBrands = ()=>{

      const term = brandSearch.value.trim().toLowerCase();

      let visible = 0;

      brandCards.forEach(card=>{

        const match = !term || (card.dataset.brandName || "").includes(term);

        card.classList.toggle("hidden", !match);

        if(match) visible += 1;

      });

      if(brandEmpty){

        // Only show empty state if there's a search term and no results
        brandEmpty.hidden = (visible !== 0) || !term;

      }

    };

    brandSearch.addEventListener("input", filterBrands);

  } else if(brandEmpty){
    // If no brand search or cards, ensure empty state is hidden
    brandEmpty.hidden = true;
  }



  const openBrandDetail = card=>{

    const url = card.dataset.brandUrl;

    if(url){

      window.location.assign(url);

    }

  };



  brandCards.forEach(card=>{
    const openBtn = card.querySelector("[data-open-brand]");
    if(openBtn){
      openBtn.addEventListener("click", evt=>{
        evt.stopPropagation();
        openBrandDetail(card);
      });
    }
    card.addEventListener("click", ()=> openBrandDetail(card));

    card.addEventListener("keydown", evt=>{

      if(evt.key === "Enter" || evt.key === " "){

        evt.preventDefault();

        openBrandDetail(card);

      }

    });

  });



  const brandModals = document.querySelectorAll(".brand-modal");

  const openBrandModal = modal => modal && modal.classList.add("show");

  const closeBrandModal = modal => modal && modal.classList.remove("show");



  brandModals.forEach(backdrop=>{

    backdrop.addEventListener("click", evt=>{

      if(evt.target === backdrop){

        closeBrandModal(backdrop);

      }

    });

  });



  document.querySelectorAll("[data-brand-modal-close]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      closeBrandModal(btn.closest(".brand-modal"));

    });

  });



  const addBrandFab = document.getElementById("addBrandFab");

  const addBrandModal = document.getElementById("addBrandModal");

  if(addBrandFab && addBrandModal){

    addBrandFab.addEventListener("click", ()=> openBrandModal(addBrandModal));

  }



  const renameBrandModal = document.getElementById("renameBrandModal");

  const renameBrandId = document.getElementById("renameBrandId");

  const renameBrandName = document.getElementById("renameBrandName");



  document.querySelectorAll("[data-rename-brand]").forEach(btn=>{

    btn.addEventListener("click", evt=>{

      evt.stopPropagation();

      if(renameBrandModal && renameBrandId && renameBrandName){

        renameBrandId.value = btn.dataset.brandId || "";

        renameBrandName.value = btn.dataset.brandName || "";

        openBrandModal(renameBrandModal);

      }

    });

  });



  document.addEventListener("keydown", evt=>{

    if(evt.key === "Escape"){

      brandModals.forEach(closeBrandModal);

    }

  });

  const categoryModals = document.querySelectorAll(".category-modal");
  const openCategoryModal = modal => modal && modal.classList.add("show");
  const closeCategoryModal = modal => modal && modal.classList.remove("show");

  categoryModals.forEach(backdrop=>{
    backdrop.addEventListener("click", evt=>{
      if(evt.target === backdrop){
        closeCategoryModal(backdrop);
      }
    });
  });

  document.querySelectorAll("[data-category-modal-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeCategoryModal(btn.closest(".category-modal"));
    });
  });

  const addCategoryFab = document.getElementById("addCategoryFab");
  const addCategoryModal = document.getElementById("addCategoryModal");
  if(addCategoryFab && addCategoryModal){
    addCategoryFab.addEventListener("click", ()=> openCategoryModal(addCategoryModal));
  }

  const renameCategoryModal = document.getElementById("renameCategoryModal");
  const renameCategoryId = document.getElementById("renameCategoryId");
  const renameCategoryName = document.getElementById("renameCategoryName");

  document.querySelectorAll("[data-rename-category]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      if(renameCategoryModal && renameCategoryId && renameCategoryName){
        renameCategoryId.value = btn.dataset.categoryId || "";
        renameCategoryName.value = btn.dataset.categoryName || "";
        openCategoryModal(renameCategoryModal);
      }
    });
  });

  document.addEventListener("keydown", evt=>{
    if(evt.key === "Escape"){
      categoryModals.forEach(closeCategoryModal);
    }
  });


  const customerSearchInput = document.getElementById("customerSearch");
  const customerRows = Array.from(document.querySelectorAll("[data-customer-row]"));
  const customerPrevBtn = document.getElementById("customerPrevBtn");
  const customerNextBtn = document.getElementById("customerNextBtn");
  const customerPageMeta = document.getElementById("customerPageMeta");
  const customerPageSize = 10;
  let customerPage = 1;

  const getCustomerMatches = ()=>{
    const term = (customerSearchInput?.value || "").trim().toLowerCase();
    return customerRows.filter(row=>{
      const haystack = (row.dataset.customerFilter || "").toLowerCase();
      return !term || haystack.includes(term);
    });
  };

  const renderCustomerPage = ()=>{
    if(!customerRows.length){
      return;
    }
    const matches = getCustomerMatches();
    const total = matches.length;
    const totalPages = Math.max(1, Math.ceil(total / customerPageSize));
    if(customerPage > totalPages){
      customerPage = totalPages;
    }
    const start = (customerPage - 1) * customerPageSize;
    const end = start + customerPageSize;

    customerRows.forEach(row=>{
      row.hidden = true;
    });

    matches.slice(start, end).forEach(row=>{
      row.hidden = false;
    });

    if(customerPageMeta){
      if(total === 0){
        customerPageMeta.textContent = "Showing 0 of 0";
      } else {
        customerPageMeta.textContent = `Showing ${start + 1}-${Math.min(end, total)} of ${total}`;
      }
    }

    if(customerPrevBtn){
      customerPrevBtn.disabled = customerPage <= 1;
    }
    if(customerNextBtn){
      customerNextBtn.disabled = customerPage >= totalPages;
    }
  };

  if(customerRows.length){
    renderCustomerPage();
    customerSearchInput?.addEventListener("input", ()=>{
      customerPage = 1;
      renderCustomerPage();
    });
    customerPrevBtn?.addEventListener("click", ()=>{
      if(customerPage > 1){
        customerPage -= 1;
        renderCustomerPage();
      }
    });
    customerNextBtn?.addEventListener("click", ()=>{
      const matches = getCustomerMatches();
      const totalPages = Math.max(1, Math.ceil(matches.length / customerPageSize));
      if(customerPage < totalPages){
        customerPage += 1;
        renderCustomerPage();
      }
    });
  }


  const saleReturnBase = 0;

  const productCards = document.querySelectorAll("[data-product-card]");

  const productSearchInput = document.getElementById("productSearch");

  const productCategoryFilter = document.getElementById("productCategoryFilter");

  const productBrandFilter = document.getElementById("productBrandFilter");

  const productEmptyState = document.getElementById("productEmpty");

  const productPagination = document.getElementById("productPagination");

  const productPrevBtn = document.getElementById("productPrevBtn");

  const productNextBtn = document.getElementById("productNextBtn");

  const productPageMeta = document.getElementById("productPageMeta");

  const visibleProductCount = document.getElementById("visibleProductCount");

  const stockFilterButtons = document.querySelectorAll("[data-stock-filter]");

  const productPageSize = 12;

  let productPage = 1;

  let activeStockFilter = "";
  let productFiltersTouched = false;



  const applyProductFilters = ()=>{

    if(!productCards.length){

      return;

    }

    const term = (productSearchInput?.value || "").trim().toLowerCase();

    const category = productCategoryFilter?.value || "";

    const brand = productBrandFilter?.value || "";

    const matches = [];

    productCards.forEach(card=>{

      const matchesTerm = !term || (card.dataset.productName || "").includes(term);

      const matchesCategory = !category || (card.dataset.productCategory || "") === category;

      const matchesBrand = !brand || (card.dataset.productBrand || "") === brand;

      const matchesStock = !activeStockFilter || (card.dataset.productStock || "") === activeStockFilter;

      if(matchesTerm && matchesCategory && matchesBrand && matchesStock){

        matches.push(card);

      }

    });

    const total = matches.length;
    const totalPages = Math.max(1, Math.ceil(total / productPageSize));
    if(productPage > totalPages){
      productPage = totalPages;
    }
    const start = (productPage - 1) * productPageSize;
    const end = Math.min(start + productPageSize, total);

    productCards.forEach(card=>{
      card.classList.add("hidden");
    });
    matches.slice(start, end).forEach(card=>{
      card.classList.remove("hidden");
    });

    if(productEmptyState){
      const anyFilterActive = term || category || brand || activeStockFilter;
      const shouldShow = productFiltersTouched && anyFilterActive && total === 0;
      productEmptyState.hidden = !shouldShow;
    }

    if(visibleProductCount){
      if(total === 0){
        visibleProductCount.textContent = "No products match these filters.";
      }else if(total > productPageSize){
        visibleProductCount.textContent = `Showing ${start + 1}-${end} of ${total} products.`;
      }else{
        visibleProductCount.textContent = `Showing ${total} product${total === 1 ? "" : "s"}.`;
      }
    }

    if(productPageMeta){
      productPageMeta.textContent = total
        ? `Page ${productPage} of ${totalPages}`
        : "Page 0 of 0";
    }
    if(productPrevBtn){
      productPrevBtn.disabled = productPage <= 1;
    }
    if(productNextBtn){
      productNextBtn.disabled = productPage >= totalPages;
    }
    if(productPagination){
      productPagination.hidden = total <= productPageSize;
    }

  };



  // Only set up product filters if we're on the products page
  if(productCards.length > 0){
    productSearchInput?.addEventListener("input", ()=>{
      productFiltersTouched = true;
      productPage = 1;
      applyProductFilters();
    });
    productCategoryFilter?.addEventListener("change", ()=>{
      productFiltersTouched = true;
      productPage = 1;
      applyProductFilters();
    });
    productBrandFilter?.addEventListener("change", ()=>{
      productFiltersTouched = true;
      productPage = 1;
      applyProductFilters();
    });
    stockFilterButtons.forEach(btn=>{
      btn.addEventListener("click", ()=>{
        stockFilterButtons.forEach(chip=> chip.classList.remove("active"));
        btn.classList.add("active");
        activeStockFilter = btn.dataset.stockFilter || "";
        productFiltersTouched = true;
        productPage = 1;
        applyProductFilters();
      });
    });
    productPrevBtn?.addEventListener("click", ()=>{
      if(productPage > 1){
        productPage -= 1;
        applyProductFilters();
      }
    });
    productNextBtn?.addEventListener("click", ()=>{
      productPage += 1;
      applyProductFilters();
    });
    // Initialize filters on page load to set correct initial state
    productEmptyState && (productEmptyState.hidden = true);
    applyProductFilters();
  }



  const productModals = document.querySelectorAll(".manage-modal");

  const openProductModal = modal => modal && modal.classList.add("show");

  const closeProductModal = modal => modal && modal.classList.remove("show");



  productModals.forEach(backdrop=>{

    backdrop.addEventListener("click", evt=>{

      if(evt.target === backdrop){

        closeProductModal(backdrop);

      }

    });

  });



  document.querySelectorAll("[data-product-modal-close]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      closeProductModal(btn.closest(".manage-modal"));

    });

  });



  const editProductModal = document.getElementById("editProductModal");

  const editProductId = document.getElementById("editProductId");

  const editProductName = document.getElementById("editProductName");

  const editProductReorder = document.getElementById("editProductReorder");

  const editProductBrand = document.getElementById("editProductBrand");

  const editProductCategory = document.getElementById("editProductCategory");



  document.querySelectorAll("[data-edit-product]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      if(!editProductModal){

        return;

      }

      if(editProductId){

        editProductId.value = btn.dataset.productId || "";

      }

      if(editProductName){

        editProductName.value = btn.dataset.productName || "";

      }

      if(editProductBrand){

        editProductBrand.value = btn.dataset.productBrand || "";

      }

      if(editProductCategory){

        editProductCategory.value = btn.dataset.productCategory || "";

      }

      if(editProductReorder){

        editProductReorder.value = btn.dataset.productReorder || "3";

      }

      openProductModal(editProductModal);

    });

  });



  document.addEventListener("keydown", evt=>{

    if(evt.key === "Escape"){

      productModals.forEach(closeProductModal);

    }

  });



  const checklist = document.getElementById("batchProductChecklist");

  const batchSearchInput = document.getElementById("batchProductSearch");

  const prepareBatchBtn = document.getElementById("prepareBatchBtn");

  const multiBatchCard = document.getElementById("multiBatchCard");

  const batchEntryContainer = document.getElementById("batchEntryContainer");

  const resetBatchSelection = document.getElementById("resetBatchSelection");

  const selectionHint = document.getElementById("batchSelectionHint");

  const defaultBatchDate = 0;
  const openStockPicker = document.getElementById("openStockPicker");
  const stockPickerModal = document.getElementById("stockPickerModal");


  const openStockPickerModal = ()=>{

    if(!stockPickerModal){

      return;

    }

    stockPickerModal.classList.add("show");

    batchSearchInput?.focus();

  };

  const closeStockPickerModal = ()=>{

    stockPickerModal?.classList.remove("show");

  };



  const buildBatchRow = (productId, productName, defaults = {})=>{

    const purchaseDefault = defaults.purchaseRate || "";

    const saleDefault = defaults.salePrice || "";

    const wrapper = document.createElement("div");

    wrapper.className = "batch-entry";

    wrapper.innerHTML = `

      <div class="batch-entry-head">

        <strong>${productName}</strong>

        <input type="hidden" name="batch_product_id[]" value="${productId}">

      </div>

      <div class="batch-entry-grid">

        <label>

          <span>Quantity</span>

          <input type="number" name="batch_quantity[]" min="1" required placeholder="0">

        </label>

        <label>

          <span>Purchase rate (PKR)</span>

          <input type="number" step="0.01" min="0" name="batch_purchase_rate[]" required placeholder="0.00" value="${purchaseDefault}">

        </label>

        <label>

          <span>Sale price (PKR)</span>

          <input type="number" step="0.01" min="0" name="batch_sale_price[]" required placeholder="0.00" value="${saleDefault}">

        </label>

      </div>

    `;

    return wrapper;

  };

  openStockPicker?.addEventListener("click", openStockPickerModal);

  document.querySelectorAll("[data-stock-picker-close]").forEach(btn=>{

    btn.addEventListener("click", closeStockPickerModal);

  });

  stockPickerModal?.addEventListener("click", evt=>{

    if(evt.target === stockPickerModal){

      closeStockPickerModal();

    }

  });



  if(prepareBatchBtn && checklist && batchEntryContainer){

    prepareBatchBtn.addEventListener("click", ()=>{

      const checked = checklist.querySelectorAll("input[type='checkbox']:checked");

      if(!checked.length){

        selectionHint.textContent = "Pick at least one product to continue.";

        selectionHint.classList.add("error");

        return;

      }

      selectionHint.textContent = `${checked.length} product(s) selected.`;

      selectionHint.classList.remove("error");



      batchEntryContainer.innerHTML = "";

      checked.forEach(input=>{

        const name = input.dataset.productName || "Product";

        const defaults = {

          purchaseRate: input.dataset.purchaseRate || "",

          salePrice: input.dataset.salePrice || "",

        };

        batchEntryContainer.appendChild(buildBatchRow(input.value, name, defaults));

      });

      closeStockPickerModal();

      multiBatchCard.hidden = false;

      multiBatchCard.scrollIntoView({behavior:"smooth"});

    });

  }



  if(resetBatchSelection && multiBatchCard){

    resetBatchSelection.addEventListener("click", ()=>{

      multiBatchCard.hidden = true;

      batchEntryContainer.innerHTML = "";

      openStockPickerModal();

    });

  }



  if(batchSearchInput && checklist){

    const productCards = checklist.querySelectorAll(".restock-pick-row");

    const filterProducts = ()=>{

      const term = batchSearchInput.value.trim().toLowerCase();

      let visible = 0;

      productCards.forEach(card=>{

        const name = card.dataset.productName || "";
        const category = card.dataset.productCategory || "";
        const match = !term || name.includes(term) || category.includes(term);

        card.classList.toggle("hidden", !match);

        if(match) visible += 1;

      });

      if(term){
        selectionHint.textContent = visible ? `Showing ${visible} product(s)` : "No products match this search.";
      } else {
        selectionHint.textContent = visible ? `${visible} product(s) available` : "Pick at least one product to continue.";
      }

    };

    batchSearchInput.addEventListener("input", filterProducts);

  }



  const saleChecklist = document.getElementById("saleProductChecklist");
  const saleSearchInput = document.getElementById("saleProductSearch");
  const prepareSaleBtn = document.getElementById("prepareSaleBtn");
  const saleEntryContainer = document.getElementById("saleEntryContainer");
  const multiSaleCard = document.getElementById("multiSaleCard");
  const resetSaleSelection = document.getElementById("resetSaleSelection");
  const saleSelectionHint = document.getElementById("saleSelectionHint");
  const openSalePicker = document.getElementById("openSalePicker");
  const salePickerModal = document.getElementById("salePickerModal");
  const saleCustomerId = document.getElementById("saleCustomerId");
  const saleCustomerLabel = document.getElementById("saleCustomerLabel");
  const openCustomerPicker = document.getElementById("openCustomerPicker");
  const clearCustomerPicker = document.getElementById("clearCustomerPicker");
  const customerPickerModal = document.getElementById("customerPickerModal");
  const customerPickerSearch = document.getElementById("customerPickerSearch");
  const customerPickerList = document.getElementById("customerPickerList");
  const customerPickerEmpty = document.getElementById("customerPickerEmpty");
  const openCustomerCreate = document.getElementById("openCustomerCreate");
  const customerCreateModal = document.getElementById("customerCreateModal");
  const customerCreateName = document.getElementById("customerCreateName");
  const customerCreatePhone = document.getElementById("customerCreatePhone");
  const customerCreateForm = document.getElementById("customerCreateForm");
  const saleDraftKey = "ezzystore.saleDraft";
  const expensePercent = Number(0) || 0;

  const getExpensePrice = (purchaseRate)=>{
    if(purchaseRate === "" || purchaseRate === null || purchaseRate === undefined){
      return "";
    }
    const base = Number(purchaseRate);
    if(!Number.isFinite(base)){
      return "";
    }
    if(expensePercent <= 0){
      return base.toFixed(2);
    }
    return (base * (1 + (expensePercent / 100))).toFixed(2);
  };



  const buildSaleDraft = ()=>{

    if(!saleChecklist){

      return null;

    }

    const entries = [];

    if(saleEntryContainer && saleEntryContainer.children.length){

      saleEntryContainer.querySelectorAll(".batch-entry").forEach(entry=>{

        const id = entry.querySelector("input[name='sale_product_id[]']")?.value;

        if(!id){

          return;

        }

        const quantity = entry.querySelector("input[name='sale_quantity[]']")?.value || "";

        const price = entry.querySelector("input[name='sale_price[]']")?.value || "";

        const expense = entry.querySelector("input[name='sale_expense[]']")?.value || "0";

        entries.push({ id, quantity, price, expense });

      });

      return entries.length ? { stage: "details", entries } : null;

    }

    const checked = saleChecklist.querySelectorAll("input[type='checkbox']:checked");

    checked.forEach(input=>{

      entries.push({ id: input.value, price: input.dataset.salePrice || "" });

    });

    return entries.length ? { stage: "select", entries } : null;

  };

  const saveSaleDraft = ()=>{

    const draft = buildSaleDraft();

    if(draft){

      sessionStorage.setItem(saleDraftKey, JSON.stringify(draft));

    }else{

      sessionStorage.removeItem(saleDraftKey);

    }

  };

  const restoreSaleDraft = ()=>{

    if(!saleChecklist){

      return;

    }

    const raw = sessionStorage.getItem(saleDraftKey);

    if(!raw){

      return;

    }

    let draft = null;

    try{

      draft = JSON.parse(raw);

    }catch(err){

      sessionStorage.removeItem(saleDraftKey);

      return;

    }

    if(!draft || !Array.isArray(draft.entries) || !draft.entries.length){

      sessionStorage.removeItem(saleDraftKey);

      return;

    }

    const entryMap = new Map(draft.entries.map(entry=>[String(entry.id), entry]));

    saleChecklist.querySelectorAll("input[type='checkbox']").forEach(input=>{

      input.checked = entryMap.has(String(input.value));

    });

    if(draft.stage === "details" && prepareSaleBtn && saleEntryContainer){

      prepareSaleBtn.click();

      saleEntryContainer.querySelectorAll(".batch-entry").forEach(entry=>{

        const id = entry.querySelector("input[name='sale_product_id[]']")?.value;

        if(!id){

          return;

        }

        const data = entryMap.get(String(id));

        if(!data){

          return;

        }

        const qtyInput = entry.querySelector("input[name='sale_quantity[]']");

        const priceInput = entry.querySelector("input[name='sale_price[]']");

        if(qtyInput && data.quantity !== undefined){

          qtyInput.value = data.quantity;

        }

        if(priceInput && data.price !== undefined){

          priceInput.value = data.price;

        }

        const expenseToggle = entry.querySelector("[data-expense-toggle]");
        const expenseFlag = entry.querySelector("input[name='sale_expense[]']");
        const useExpense = String(data.expense || "0") === "1";
        if(expenseFlag){
          expenseFlag.value = useExpense ? "1" : "0";
        }
        if(expenseToggle){
          expenseToggle.checked = useExpense;
          if(useExpense){
            expenseToggle.dispatchEvent(new Event("change"));
          }
        }

      });

    }else if(saleSelectionHint){

      saleSelectionHint.textContent = `${entryMap.size} product(s) selected.`;

      saleSelectionHint.classList.remove("error");

    }

    sessionStorage.removeItem(saleDraftKey);

  };

  const openSalePickerModal = ()=>{

    if(!salePickerModal){

      return;

    }

    salePickerModal.classList.add("show");

    saleSearchInput?.focus();

  };

  const closeSalePickerModal = ()=>{

    salePickerModal?.classList.remove("show");

  };

  const buildSaleRow = (productId, productName, defaults = {})=>{

    const salePriceDefault = defaults.salePrice || "";
    const purchaseRate = defaults.purchaseRate || "";

    const wrapper = document.createElement("div");

    wrapper.className = "batch-entry";

    wrapper.innerHTML = `

      <div class="batch-entry-head">

        <strong>${productName}</strong>

        <input type="hidden" name="sale_product_id[]" value="${productId}">

      </div>

      <div class="batch-entry-grid">

        <label>

          <span>Quantity</span>

          <input type="number" name="sale_quantity[]" min="1" required placeholder="0">

        </label>

        <label>

          <span>Sale price (PKR)</span>

          <input type="number" step="0.01" min="0" name="sale_price[]" required placeholder="0.00" value="${salePriceDefault}">

        </label>

      </div>

      <div class="batch-entry-foot">

        <input type="hidden" name="sale_expense[]" value="0" data-expense-flag>

        <label class="expense-toggle">

          <input type="checkbox" data-expense-toggle>

          <span>Sell with expense (no profit)</span>

        </label>

      </div>

    `;

    const priceInput = wrapper.querySelector("input[name='sale_price[]']");
    const expenseFlag = wrapper.querySelector("[data-expense-flag]");
    const expenseToggle = wrapper.querySelector("[data-expense-toggle]");

    const applyExpenseToggle = (enabled)=>{
      if(!priceInput || !expenseFlag || !expenseToggle){
        return;
      }
      if(enabled){
        const purchase = Number(purchaseRate);
        if(!Number.isFinite(purchase)){
          alert("This product has no purchase rate yet. Add a restock purchase price first.");
          expenseToggle.checked = false;
          expenseFlag.value = "0";
          return;
        }
        priceInput.dataset.prevPrice = priceInput.value || salePriceDefault || "";
        priceInput.value = getExpensePrice(purchase);
        priceInput.readOnly = true;
        priceInput.classList.add("is-locked");
        expenseFlag.value = "1";
      }else{
        const restore = priceInput.dataset.prevPrice || salePriceDefault || "";
        priceInput.value = restore;
        priceInput.readOnly = false;
        priceInput.classList.remove("is-locked");
        expenseFlag.value = "0";
      }
    };

    expenseToggle?.addEventListener("change", ()=>{
      applyExpenseToggle(expenseToggle.checked);
    });

    return wrapper;

  };

  openSalePicker?.addEventListener("click", openSalePickerModal);

  document.querySelectorAll("[data-sale-picker-close]").forEach(btn=>{

    btn.addEventListener("click", closeSalePickerModal);

  });

  salePickerModal?.addEventListener("click", evt=>{

    if(evt.target === salePickerModal){

      closeSalePickerModal();

    }

  });



  if(prepareSaleBtn && saleChecklist && saleEntryContainer){

    prepareSaleBtn.addEventListener("click", ()=>{

      const checked = saleChecklist.querySelectorAll("input[type='checkbox']:checked");

      if(!checked.length){

        saleSelectionHint.textContent = "Pick at least one product to continue.";

        saleSelectionHint.classList.add("error");

        return;

      }

      saleSelectionHint.textContent = `${checked.length} product(s) selected.`;

      saleSelectionHint.classList.remove("error");

      saleEntryContainer.innerHTML = "";

      checked.forEach(input=>{

        const name = input.dataset.productName || "Product";

        const defaults = {

          salePrice: input.dataset.salePrice || "",
          purchaseRate: input.dataset.purchaseRate || "",

        };

        saleEntryContainer.appendChild(buildSaleRow(input.value, name, defaults));

      });

      multiSaleCard.hidden = false;

      multiSaleCard.scrollIntoView({behavior:"smooth"});

      closeSalePickerModal();

    });

  }



  if(resetSaleSelection && multiSaleCard){

    resetSaleSelection.addEventListener("click", ()=>{

      multiSaleCard.hidden = true;

      saleEntryContainer.innerHTML = "";

      openSalePickerModal();

    });

  }



  if(saleSearchInput && saleChecklist){

    const saleCards = saleChecklist.querySelectorAll(".checkbox-card");

    const filterSaleProducts = ()=>{

      const term = saleSearchInput.value.trim().toLowerCase();

      let visible = 0;

      saleCards.forEach(card=>{

        const match = !term || (card.dataset.saleProductName || "").includes(term);

        card.classList.toggle("hidden", !match);

        if(match){

          visible += 1;

        }

      });

      if(term){
        saleSelectionHint.textContent = visible ? `Showing ${visible} product(s)` : "No products match this search.";
      } else {
        saleSelectionHint.textContent = visible ? `${visible} product(s) available` : "Pick at least one product to continue.";
      }

    };

    saleSearchInput.addEventListener("input", filterSaleProducts);

  }

  restoreSaleDraft();

  const reportDateSearch = document.getElementById("reportDateSearch");
  const reportCards = document.querySelectorAll("[data-report-date]");
  const reportSearchEmpty = document.getElementById("reportSearchEmpty");

  const filterReportCards = ()=>{
    if(!reportCards.length){
      reportSearchEmpty?.setAttribute("hidden", "hidden");
      return;
    }
    const term = (reportDateSearch?.value || "").trim().toLowerCase();
    let visible = 0;
    reportCards.forEach(card=>{
      const haystack = (card.dataset.reportDate || "").toLowerCase();
      const show = !term || haystack.includes(term);
      card.classList.toggle("hidden", !show);
      if(show){
        visible += 1;
      }
    });
    if(reportSearchEmpty){
      if(visible === 0 && term){
        reportSearchEmpty.removeAttribute("hidden");
      }else{
        reportSearchEmpty.setAttribute("hidden", "hidden");
      }
    }
  };

  reportDateSearch?.addEventListener("input", filterReportCards);

  const customerLookup = 0;

  const updateCustomerDisplay = (id)=>{

    if(!saleCustomerLabel){

      return;

    }

    const customer = customerLookup.find(c=> String(c.id) === String(id));

    if(customer){

      saleCustomerLabel.textContent = customer.phone ? `${customer.name} · ${customer.phone}` : customer.name;

      clearCustomerPicker?.removeAttribute("hidden");

    }else{

      saleCustomerLabel.textContent = "Select customer";

      clearCustomerPicker?.setAttribute("hidden", "hidden");

    }

  };

  const filterCustomerPicker = ()=>{

    if(!customerPickerList){

      return;

    }

    const term = (customerPickerSearch?.value || "").trim().toLowerCase();

    let visible = 0;

    customerPickerList.querySelectorAll("[data-customer-option]").forEach(btn=>{

      const haystack = `${btn.dataset.customerName || ""} ${btn.dataset.customerPhone || ""}`.toLowerCase();

      const show = !term || haystack.includes(term);

      btn.hidden = !show;

      if(show){

        visible += 1;

      }

    });

    if(customerPickerEmpty){

      // Only show empty state if there's a search term and no results
      customerPickerEmpty.hidden = (visible !== 0) || !term;

    }

  };

  const openCustomerPickerModal = ()=>{

    if(!customerPickerModal){

      return;

    }

    customerPickerModal.classList.add("show");

    if(customerPickerSearch){

      customerPickerSearch.value = "";

      filterCustomerPicker();

      customerPickerSearch.focus();

    }

  };

  const closeCustomerPickerModal = ()=>{

    customerPickerModal?.classList.remove("show");

  };

  const openCustomerCreateModal = ()=>{

    if(!customerCreateModal){

      return;

    }

    customerCreateModal.classList.add("show");

    if(customerCreateName){

      customerCreateName.value = "";

      if(customerCreatePhone){
        customerCreatePhone.value = "";
      }

      customerCreateName.focus();

    }

  };

  const closeCustomerCreateModal = ()=>{

    customerCreateModal?.classList.remove("show");

  };

  const applyCustomerSelection = id=>{

    if(!saleCustomerId){

      return;

    }

    saleCustomerId.value = id || "";

    updateCustomerDisplay(id);

    closeCustomerPickerModal();

    showSection("sales");

    multiSaleCard?.scrollIntoView({behavior:"smooth"});

  };

  openCustomerPicker?.addEventListener("click", openCustomerPickerModal);
  openCustomerCreate?.addEventListener("click", openCustomerCreateModal);
  customerCreateForm?.addEventListener("submit", saveSaleDraft);

  customerPickerSearch?.addEventListener("input", filterCustomerPicker);

  clearCustomerPicker?.addEventListener("click", ()=>{

    if(!saleCustomerId){

      return;

    }

    saleCustomerId.value = "";

    updateCustomerDisplay("");

  });

  document.querySelectorAll("[data-customer-picker-close]").forEach(btn=>{

    btn.addEventListener("click", closeCustomerPickerModal);

  });

  document.querySelectorAll("[data-customer-create-close]").forEach(btn=>{

    btn.addEventListener("click", closeCustomerCreateModal);

  });

  customerPickerModal?.addEventListener("click", evt=>{

    if(evt.target === customerPickerModal){

      closeCustomerPickerModal();

    }

  });

  customerCreateModal?.addEventListener("click", evt=>{

    if(evt.target === customerCreateModal){

      closeCustomerCreateModal();

    }

  });

  customerPickerList?.addEventListener("click", evt=>{

    const btn = evt.target.closest("[data-customer-option]");

    if(!btn){

      return;

    }

    applyCustomerSelection(btn.dataset.customerOption || "");

  });

  document.getElementById("customersSection")?.addEventListener("click", evt=>{

    const btn = evt.target.closest("[data-customer-option]");

    if(!btn){

      return;

    }

    applyCustomerSelection(btn.dataset.customerOption || "");

  });

  updateCustomerDisplay(saleCustomerId?.value || "");



  const returnSaleModal = document.getElementById("returnSaleModal");

  const returnSaleForm = document.getElementById("returnSaleForm");

  const returnSaleContainer = document.getElementById("returnSaleContainer");

  const returnSaleConfirm = document.getElementById("returnSaleConfirm");

  const confirmReturnBtn = document.getElementById("confirmReturnBtn");

  const normalizeReturnItems = (items = [])=>{
    return items
      .map(item=>{
        const soldQty = Number(item.quantity) || 0;
        const remaining = Math.min(
          soldQty,
          Math.max(Number(item.remaining_quantity ?? soldQty) || 0, 0)
        );
        return { ...item, __soldQty: soldQty, __remainingQty: remaining };
      })
      .filter(entry=> entry.__remainingQty > 0);
  };

  const refreshReturnButtonState = ()=>{

    if(!confirmReturnBtn){

      return;

    }

    const selected = returnSaleContainer?.querySelector(".return-item-toggle:checked");

    confirmReturnBtn.disabled = !(returnSaleConfirm?.checked && selected);

  };



  const openReturnModal = (saleId, saleItemsData, { autoSelect = false } = {})=>{

    if(!returnSaleModal || !returnSaleForm || !returnSaleContainer || !returnSaleConfirm || !confirmReturnBtn){

      return;

    }

    if(!saleId || !saleItemsData.length){

      return;

    }

    const eligibleItems = normalizeReturnItems(saleItemsData);

    if(!eligibleItems.length){

      alert("All items from this sale have already been returned.");

      return;

    }

    returnSaleForm.action = saleReturnBase.replace("/0/return", `/${saleId}/return`);

    returnSaleContainer.innerHTML = "";

    eligibleItems.forEach(item=>{

      const entryId = `return-item-${item.id}`;

      const soldQty = item.__soldQty;

      const remainingQty = item.__remainingQty;

      const qtyLabel = remainingQty === soldQty
        ? `Return quantity (max ${soldQty})`
        : `Return quantity (left ${remainingQty} of ${soldQty})`;

      const wrapper = document.createElement("div");

      wrapper.className = "batch-entry";

      wrapper.innerHTML = `

        <div class="batch-entry-head">

          <label class="return-select">

            <input type="checkbox" class="return-item-toggle" data-entry="${entryId}">

            <span>${item.product_name}</span>

          </label>

          <input type="hidden" name="return_sale_item_id[]" value="${item.id}" data-return-field="${entryId}" disabled>

          <input type="hidden" name="return_price[]" value="${item.unit_price}" data-return-field="${entryId}" disabled>

        </div>

        <div class="batch-entry-grid">

          <label>

            <span>${qtyLabel}</span>

            <input type="number" name="return_quantity[]" min="1" max="${remainingQty}" value="${remainingQty}" required data-return-field="${entryId}" disabled>

          </label>

          <label>

            <span>Unit price (PKR)</span>

            <input type="number" value="${item.unit_price}" readonly>

          </label>

        </div>

      `;

      returnSaleContainer.appendChild(wrapper);

      const toggle = wrapper.querySelector(".return-item-toggle");

      const toggleFields = checked=>{

        wrapper.querySelectorAll(`[data-return-field="${entryId}"]`).forEach(input=>{

          input.disabled = !checked;

        });

      };

      toggle?.addEventListener("change", ()=>{

        toggleFields(toggle.checked);

        refreshReturnButtonState();

      });

      const initialState = autoSelect;

      toggle.checked = initialState;

      toggleFields(initialState);

    });

    returnSaleConfirm.checked = false;

    refreshReturnButtonState();

    returnSaleModal.classList.add("show");

  };



  document.querySelectorAll("[data-return-sale]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      const saleId = btn.dataset.saleId;

      const saleItemsData = btn.dataset.saleItems ? JSON.parse(btn.dataset.saleItems) : [];

      openReturnModal(saleId, saleItemsData, { autoSelect: false });

    });

  });



  document.querySelectorAll("[data-return-sale-item]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      const saleId = btn.dataset.saleId;

      const itemData = btn.dataset.saleItem ? JSON.parse(btn.dataset.saleItem) : null;

      if(!itemData){

        return;

      }

      openReturnModal(saleId, [itemData], { autoSelect: true });

    });

  });

  returnSaleConfirm?.addEventListener("change", ()=>{

    refreshReturnButtonState();

  });



  document.querySelectorAll("[data-return-modal-close]").forEach(btn=>{

    btn.addEventListener("click", ()=>{

      returnSaleModal?.classList.remove("show");

    });

  });



  returnSaleModal?.addEventListener("click", evt=>{

    if(evt.target === returnSaleModal){

      returnSaleModal.classList.remove("show");

    }

  });

