

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
      setManagerDrawerOpen(false);

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
  const openManagerDrawerButtons = document.querySelectorAll("[data-open-manager-drawer]");
  const closeManagerDrawer = document.getElementById("closeManagerDrawer");
  const managerDrawer = document.getElementById("managerDrawer");
  const managerDrawerBackdrop = document.getElementById("managerDrawerBackdrop");
  const customerPageSize = 10;
  let customerPage = 1;

  const setManagerDrawerOpen = isOpen=>{
    if(!managerDrawer || !managerDrawerBackdrop){
      return;
    }
    managerDrawer.classList.toggle("is-open", isOpen);
    managerDrawerBackdrop.hidden = !isOpen;
    document.body.classList.toggle("drawer-open", isOpen);
  };

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

  openManagerDrawerButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      setManagerDrawerOpen(true);
    });
  });
  closeManagerDrawer?.addEventListener("click", ()=>{
    setManagerDrawerOpen(false);
  });
  managerDrawerBackdrop?.addEventListener("click", ()=>{
    setManagerDrawerOpen(false);
  });
  managerDrawer?.querySelectorAll("a")?.forEach(link=>{
    link.addEventListener("click", ()=>{
      setManagerDrawerOpen(false);
    });
  });


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
  const addProductModal = document.getElementById("addProductModal");
  const addProductFab = document.getElementById("addProductFab");
  const contextAddFab = document.getElementById("contextAddFab");
  const openContextAddModal = ()=>{
    if(contextAddFab){
      const targetModalId = contextAddFab.getAttribute("data-modal-open");
      if(targetModalId){
        const targetModal = document.getElementById(targetModalId);
        if(targetModal){
          targetModal.classList.add("show");
          return true;
        }
      }
    }
    return false;
  };

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
  const batchEntryContainer = document.getElementById("batchEntryContainer");
  const batchEntryBody = document.getElementById("batchEntryBody");

  const resetBatchSelection = document.getElementById("resetBatchSelection");

  const selectionHint = document.getElementById("batchSelectionHint");
  const batchSelectionPreview = document.getElementById("batchSelectionPreview");
  const batchSelectionList = document.getElementById("batchSelectionList");
  const batchSelectionCount = document.getElementById("batchSelectionCount");
  const batchDateGroup = document.getElementById("batchDateGroup");

  const defaultBatchDate = {{ today_iso|tojson }};
  const openStockPicker = document.getElementById("openStockPicker");
  const openRestockFab = document.getElementById("openRestockFab");
  const toggleQuickActions = document.getElementById("toggleQuickActions");
  const quickActionGroup = document.getElementById("quickActionGroup");
  const stockPickerModal = document.getElementById("stockPickerModal");
  const restockDetailsModal = document.getElementById("restockDetailsModal");
  const multiBatchForm = document.getElementById("multiBatchForm");


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
  const openRestockDetailsModal = ()=>{
    restockDetailsModal?.classList.add("show");
  };
  const closeRestockDetailsModal = ()=>{
    restockDetailsModal?.classList.remove("show");
  };
  const setQuickActionsOpen = (isOpen)=>{
    if(!quickActionGroup || !toggleQuickActions){
      return;
    }
    quickActionGroup.hidden = !isOpen;
    quickActionGroup.classList.toggle("is-open", isOpen);
    toggleQuickActions.classList.toggle("is-open", isOpen);
    toggleQuickActions.setAttribute("aria-expanded", isOpen ? "true" : "false");
  };
  const resetRestockWorkflow = ()=>{
    checklist?.querySelectorAll("input[type='checkbox']").forEach(input=>{
      input.checked = false;
    });
    if(batchEntryBody){
      batchEntryBody.innerHTML = "";
    }
    if(multiBatchForm){
      multiBatchForm.reset();
    }
    if(batchDateGroup){
      batchDateGroup.value = defaultBatchDate;
    }
    if(selectionHint){
      selectionHint.textContent = "Pick at least one product to continue.";
      selectionHint.classList.remove("error");
    }
    updateBatchSelectionPreview();
    closeRestockDetailsModal();
    closeStockPickerModal();
  };

  const updateBatchSelectionPreview = ()=>{

    if(!checklist || !batchSelectionPreview || !batchSelectionList){

      return;

    }

    const checked = checklist.querySelectorAll("input[type='checkbox']:checked");

    batchSelectionList.innerHTML = "";

    if(!checked.length){
      if(batchSelectionCount){
        batchSelectionCount.textContent = "(0)";
      }

      batchSelectionPreview.hidden = true;

      return;

    }

    checked.forEach(input=>{

      const name = input.dataset.productName || "Product";
      const brand = input.dataset.productBrand || "-";

      const chip = document.createElement("span");

      chip.className = "selection-chip";

      chip.textContent = brand && brand !== "-" ? `${name} (${brand})` : name;

      batchSelectionList.appendChild(chip);

    });

    if(batchSelectionCount){
      batchSelectionCount.textContent = `(${checked.length})`;
    }
    batchSelectionPreview.hidden = false;

  };



  const buildBatchRow = (productId, productName, productBrand, defaults = {}, index = 1)=>{

    const purchaseDefault = defaults.purchaseRate || "";

    const saleDefault = defaults.salePrice || "";

    const row = document.createElement("tr");

    row.innerHTML = `
      <td class="product-sr-cell">${index}</td>
      <td class="sale-item-name">
        <strong>${productName}</strong>
        <span class="sale-item-brand">${productBrand && productBrand !== "-" ? productBrand : "No brand"}</span>
        <input type="hidden" name="batch_product_id[]" value="${productId}">
      </td>
      <td>
        <input class="sale-input" type="number" name="batch_quantity[]" min="1" required placeholder="0">
      </td>
      <td>
        <input class="sale-input" type="number" step="0.01" min="0" name="batch_purchase_rate[]" required placeholder="0.00" value="${purchaseDefault}">
      </td>
      <td>
        <input class="sale-input" type="number" step="0.01" min="0" name="batch_sale_price[]" required placeholder="0.00" value="${saleDefault}">
      </td>
    `;

    return row;

  };

  openStockPicker?.addEventListener("click", openStockPickerModal);
  openRestockFab?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    openStockPickerModal();
  });
  const quickActionsModal = document.getElementById("quickActionsModal");
  toggleQuickActions?.addEventListener("click", evt=>{
    evt.preventDefault();
    evt.stopPropagation();
    quickActionsModal?.classList.add("show");
  });

  document.querySelectorAll("[data-quick-actions-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      quickActionsModal?.classList.remove("show");
    });
  });

  if(quickActionsModal){
    quickActionsModal.addEventListener("click", evt=>{
      if(evt.target === quickActionsModal){
        quickActionsModal.classList.remove("show");
      }
    });
  }

  document.querySelectorAll(".quick-action-card").forEach(card=>{
    card.addEventListener("click", ()=>{
      quickActionsModal?.classList.remove("show");
      const targetId = card.dataset.triggerBtn;
      const targetBtn = document.getElementById(targetId);
      if(targetBtn){
        targetBtn.click();
      }
    });
  });

  document.querySelectorAll("[data-stock-picker-close]").forEach(btn=>{

    btn.addEventListener("click", closeStockPickerModal);

  });

  stockPickerModal?.addEventListener("click", evt=>{

    if(evt.target === stockPickerModal){

      closeStockPickerModal();

    }

  });

  addProductFab?.addEventListener("click", ()=>{
    openProductModal(addProductModal);
  });
  contextAddFab?.addEventListener("click", evt=>{
    if(openContextAddModal()){
      evt.stopPropagation();
      return;
    }
    if(addCategoryModal && managerActivePage === "product_management" && managerCatalogTab === "categories"){
      openCategoryModal(addCategoryModal);
      return;
    }
    if(addBrandModal && managerActivePage === "product_management" && managerCatalogTab === "brands"){
      openBrandModal(addBrandModal);
      return;
    }
    if(addProductModal && managerActivePage === "product_management" && managerCatalogTab === "products"){
      openProductModal(addProductModal);
    }
  });
  document.querySelectorAll("[data-restock-details-close]").forEach(btn=>{
    btn.addEventListener("click", closeRestockDetailsModal);
  });
  restockDetailsModal?.addEventListener("click", evt=>{
    if(evt.target === restockDetailsModal){
      closeRestockDetailsModal();
    }
  });



  if(prepareBatchBtn && checklist && batchEntryContainer && batchEntryBody){

    prepareBatchBtn.addEventListener("click", ()=>{

      const checked = checklist.querySelectorAll("input[type='checkbox']:checked");

      if(!checked.length){

        selectionHint.textContent = "Pick at least one product to continue.";

        selectionHint.classList.add("error");

        return;

      }

      selectionHint.textContent = `${checked.length} product(s) selected.`;

      selectionHint.classList.remove("error");
      updateBatchSelectionPreview();



      batchEntryBody.innerHTML = "";

      checked.forEach((input, idx)=>{

        const name = input.dataset.productName || "Product";
        const brand = input.dataset.productBrand || "-";

        const defaults = {

          purchaseRate: input.dataset.purchaseRate || "",

          salePrice: input.dataset.salePrice || "",

        };

        batchEntryBody.appendChild(buildBatchRow(input.value, name, brand, defaults, idx + 1));

      });

      closeStockPickerModal();
      openRestockDetailsModal();

    });

  }



  if(resetBatchSelection){

    resetBatchSelection.addEventListener("click", ()=>{

      if(batchEntryBody){
        batchEntryBody.innerHTML = "";
      }
      updateBatchSelectionPreview();
      closeRestockDetailsModal();
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
        const brand = card.dataset.productBrand || "";
        const category = card.dataset.productCategory || "";
        const match = !term || name.includes(term) || brand.includes(term) || category.includes(term);

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

  checklist?.addEventListener("change", evt=>{

    if(evt.target && evt.target.matches("input[type='checkbox']")){

      updateBatchSelectionPreview();

    }

  });



  const saleChecklist = document.getElementById("saleProductChecklist");
  const saleSearchInput = document.getElementById("saleProductSearch");
  const prepareSaleBtn = document.getElementById("prepareSaleBtn");
  const saleEntryContainer = document.getElementById("saleEntryContainer");
  const saleEntryBody = document.getElementById("saleEntryBody");
  const saleDetailsModal = document.getElementById("saleDetailsModal");
  const resetSaleSelection = document.getElementById("resetSaleSelection");
  const openSalePicker = document.getElementById("openSalePicker");
  const salePickerModal = document.getElementById("salePickerModal");
  const saleCustomerId = document.getElementById("saleCustomerId");
  const salePaymentMethod = document.getElementById("salePaymentMethod");
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
  const saleConfirmModal = document.getElementById("saleConfirmModal");
  const confirmCustomer = document.getElementById("confirmCustomer");
  const confirmPaymentMethod = document.getElementById("confirmPaymentMethod");
  const confirmItemCount = document.getElementById("confirmItemCount");
  const confirmTotal = document.getElementById("confirmTotal");
  const confirmProfit = document.getElementById("confirmProfit");
  const confirmProfitToggle = document.getElementById("confirmProfitToggle");
  const confirmItemsToggle = document.getElementById("confirmItemsToggle");
  const confirmItemsToggleText = document.getElementById("confirmItemsToggleText");
  const confirmItemsList = document.getElementById("confirmItemsList");
  const confirmSaleSubmit = document.getElementById("confirmSaleSubmit");
  const openSaleConfirm = document.getElementById("openSaleConfirm");
  const saleForm = document.getElementById("multiSaleForm");
  const toastStack = document.getElementById("toastStack");
  let saleConfirmOpen = false;
  const saleDraftKey = "ezzystore.saleDraft";
  const expensePercent = Number({{ expense_percent|default(0)|tojson }}) || 0;
  const hideSalePrices = {{ hide_sale_prices|default(true)|tojson }};

  const dismissToast = (toast)=>{
    if(!toast || toast.dataset.hiding === "1"){
      return;
    }
    toast.dataset.hiding = "1";
    toast.classList.add("is-hiding");
    window.setTimeout(()=>{
      toast.remove();
      if(toastStack && !toastStack.children.length){
        toastStack.hidden = true;
      }
    }, 220);
  };

  const mountToast = (toast, timeout = 2600)=>{
    if(!toastStack || !toast){
      return;
    }
    toastStack.hidden = false;
    toastStack.prepend(toast);
    window.setTimeout(()=>{
      dismissToast(toast);
    }, timeout);
  };

  const showToast = (message, category = "success")=>{
    if(!message){
      return;
    }
    if(!toastStack){
      return;
    }
    const toast = document.createElement("div");
    toast.className = `toast ${category}`;
    toast.innerHTML = `
      <div class="toast-ic">${category === "success" ? "✓" : "!"}</div>
      <div class="toast-text"></div>
    `;
    toast.querySelector(".toast-text").textContent = message;
    mountToast(toast);
  };

  toastStack?.querySelectorAll(".toast").forEach(toast=>{
    mountToast(toast, 3200);
  });

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

    if(saleEntryBody && saleEntryBody.children.length){

      saleEntryBody.querySelectorAll("tr.sale-item-row").forEach(entry=>{

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

    if(draft.stage === "details" && prepareSaleBtn && saleEntryBody){

      prepareSaleBtn.click();

      saleEntryBody.querySelectorAll("tr.sale-item-row").forEach(entry=>{

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
  const openSaleDetailsModal = ()=>{
    saleDetailsModal?.classList.add("show");
  };
  const closeSaleDetailsModal = ()=>{
    saleDetailsModal?.classList.remove("show");
  };
  const resetSaleWorkflow = ()=>{
    saleChecklist?.querySelectorAll("input[type='checkbox']").forEach(input=>{
      input.checked = false;
    });
    if(saleEntryBody){
      saleEntryBody.innerHTML = "";
    }
    if(saleForm){
      saleForm.reset();
    }
    if(salePaymentMethod){
      salePaymentMethod.value = "counter";
    }
    if(saleCustomerId){
      saleCustomerId.value = "";
    }
    updateCustomerDisplay("");
    closeConfirmModal();
    closeSaleDetailsModal();
    closeSalePickerModal();
    sessionStorage.removeItem(saleDraftKey);
  };

  const buildSaleRow = (productId, productName, productBrand = "-", defaults = {}, index = 1)=>{

    const salePriceDefault = defaults.salePrice || "";
    const purchaseRate = defaults.purchaseRate || "";

    const wrapper = document.createElement("tr");
    wrapper.className = "sale-item-row";
    wrapper.dataset.purchaseRate = purchaseRate;
    wrapper.innerHTML = `
      <td class="product-sr-cell">${index}</td>
      <td>
        <div class="sale-item-name">
          <strong>${productName}</strong>
          <span class="sale-item-brand">${productBrand || "-"}</span>
        </div>
        <input type="hidden" name="sale_product_id[]" value="${productId}">
      </td>
      <td>
        <input type="number" name="sale_quantity[]" min="1" required placeholder="0" value="1" class="sale-input">
      </td>
      <td>
        <div class="sale-price-field">
          <input type="number" step="0.01" min="0" name="sale_price[]" required placeholder="0.00" value="${salePriceDefault}" class="sale-input sale-price-input is-masked">
          <button type="button" class="sale-price-toggle" data-sale-price-toggle aria-label="Show sale price">
            <span class="eye-on" aria-hidden="true"></span>
            <span class="eye-off" aria-hidden="true"></span>
          </button>
        </div>
      </td>
      <td>
        <input type="hidden" name="sale_expense[]" value="0" data-expense-flag>
        <label class="expense-toggle">
          <input type="checkbox" data-expense-toggle>
          <span>Sell with expense</span>
        </label>
      </td>
    `;

    const priceInput = wrapper.querySelector("input[name='sale_price[]']");
    const expenseFlag = wrapper.querySelector("[data-expense-flag]");
    const expenseToggle = wrapper.querySelector("[data-expense-toggle]");
    const priceToggle = wrapper.querySelector("[data-sale-price-toggle]");

    const applyExpenseToggle = (enabled)=>{
      if(!priceInput || !expenseFlag || !expenseToggle){
        return;
      }
      if(enabled){
        const purchase = Number(purchaseRate);
        if(!Number.isFinite(purchase)){
          showToast("This product has no purchase rate yet. Add a restock purchase price first.", "error");
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

    const setPriceMasked = (masked)=>{
      priceInput?.classList.toggle("is-masked", masked);
      priceToggle?.setAttribute("aria-label", masked ? "Show sale price" : "Hide sale price");
      priceToggle?.classList.toggle("is-shown", !masked);
    };

    setPriceMasked(Boolean(hideSalePrices));
    if(priceToggle){
      priceToggle.hidden = !hideSalePrices;
    }

    priceToggle?.addEventListener("click", ()=>{
      const masked = priceInput?.classList.contains("is-masked");
      setPriceMasked(!masked);
    });

    expenseToggle?.addEventListener("change", ()=>{
      applyExpenseToggle(expenseToggle.checked);
    });

    return wrapper;

  };

  openSalePicker?.addEventListener("click", openSalePickerModal);
  openSalePicker?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
  });

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

        return;

      }

      if(saleEntryBody){
        saleEntryBody.innerHTML = "";
      }

      checked.forEach((input, idx)=>{

        const name = input.dataset.productName || "Product";

        const defaults = {

          salePrice: input.dataset.salePrice || "",
          purchaseRate: input.dataset.purchaseRate || "",

        };
        const brand = input.dataset.productBrand || "-";

        saleEntryBody?.appendChild(buildSaleRow(input.value, name, brand, defaults, idx + 1));

      });

      closeSalePickerModal();
      openSaleDetailsModal();

    });

  }



  if(resetSaleSelection && saleDetailsModal){

    resetSaleSelection.addEventListener("click", ()=>{

      if(saleEntryBody){
        saleEntryBody.innerHTML = "";
      }
      closeSaleDetailsModal();
      openSalePickerModal();

    });

  }



  if(saleSearchInput && saleChecklist){

    const saleCards = saleChecklist.querySelectorAll(".sale-pick-row");

    const filterSaleProducts = ()=>{

      const term = saleSearchInput.value.trim().toLowerCase();

      let visible = 0;

      saleCards.forEach(card=>{
        const name = card.dataset.saleProductName || "";
        const brand = card.dataset.saleProductBrand || "";
        const match = !term || name.includes(term) || brand.includes(term);

        card.classList.toggle("hidden", !match);

        if(match){

          visible += 1;

        }

      });

    };

    saleSearchInput.addEventListener("input", filterSaleProducts);

  }

  document.querySelectorAll("[data-sale-details-close]").forEach(btn=>{
    btn.addEventListener("click", closeSaleDetailsModal);
  });
  saleDetailsModal?.addEventListener("click", evt=>{
    if(evt.target === saleDetailsModal){
      closeSaleDetailsModal();
    }
  });

  const openConfirmModal = ()=>{
    if(!saleConfirmModal){
      return;
    }
    saleConfirmModal.classList.add("show");
    saleConfirmOpen = true;
  };

  const closeConfirmModal = ()=>{
    saleConfirmModal?.classList.remove("show");
    saleConfirmOpen = false;
  };


  document.querySelectorAll("[data-sale-confirm-close]").forEach(btn=>{
    btn.addEventListener("click", closeConfirmModal);
  });
  saleConfirmModal?.addEventListener("click", evt=>{
    if(evt.target === saleConfirmModal){
      closeConfirmModal();
    }
  });

  const formatMoney = (value)=>{
    if(!Number.isFinite(value)){
      return "PKR 0.00";
    }
    return `PKR ${value.toFixed(2)}`;
  };

  const buildConfirmItems = (items)=>{
    if(!confirmItemsList || !confirmItemsToggleText){
      return;
    }
    confirmItemsList.innerHTML = "";
    items.forEach(item=>{
      const row = document.createElement("div");
      row.className = "confirm-item-row";
      row.innerHTML = `
        <span class="confirm-item-name">${item.name}</span>
        <span class="confirm-item-qty">x${item.qty}</span>
      `;
      confirmItemsList.appendChild(row);
    });
    if(items.length){
      confirmItemsToggleText.textContent = `Show items (${items.length})`;
    }else{
      confirmItemsToggleText.textContent = "Show items";
    }
  };

  confirmItemsToggle?.addEventListener("click", ()=>{
    if(!confirmItemsList || !confirmItemsToggleText){
      return;
    }
    const isHidden = confirmItemsList.hasAttribute("hidden");
    if(isHidden){
      confirmItemsList.removeAttribute("hidden");
      confirmItemsToggleText.textContent = "Hide items";
    }else{
      confirmItemsList.setAttribute("hidden", "");
      const count = confirmItemsList.children.length;
      confirmItemsToggleText.textContent = count ? `Show items (${count})` : "Show items";
    }
  });

  confirmProfitToggle?.addEventListener("click", ()=>{
    if(!confirmProfit){
      return;
    }
    const masked = confirmProfit.classList.contains("masked");
    confirmProfit.classList.toggle("masked", !masked);
    confirmProfitToggle?.classList.toggle("is-shown", masked);
    confirmProfitToggle?.setAttribute("aria-label", masked ? "Hide profit" : "Show profit");
  });

  const getConfirmData = ()=>{
    const rows = saleEntryBody?.querySelectorAll("tr.sale-item-row") || [];
    const items = [];
    let totalQty = 0;
    let totalAmount = 0;
    let totalProfit = 0;
    let profitValid = true;
    rows.forEach(row=>{
      const name = row.querySelector(".sale-item-name strong")?.textContent?.trim() || "Product";
      const qtyRaw = row.querySelector("input[name='sale_quantity[]']")?.value || "0";
      const priceRaw = row.querySelector("input[name='sale_price[]']")?.value || "0";
      const qty = Number(qtyRaw);
      const price = Number(priceRaw);
      const purchaseRate = Number(row.dataset.purchaseRate);
      if(Number.isFinite(qty) && qty > 0){
        totalQty += qty;
        if(Number.isFinite(price)){
          totalAmount += qty * price;
        }
        if(Number.isFinite(purchaseRate)){
          totalProfit += qty * (price - purchaseRate);
        }else{
          profitValid = false;
        }
        items.push({ name, qty });
      }
    });
    return { items, totalQty, totalAmount, totalProfit, profitValid };
  };

  const setConfirmData = ()=>{
    const customerText = saleCustomerLabel?.textContent?.trim() || "Walk-in customer";
    confirmCustomer.textContent = customerText === "Select customer" ? "Walk-in customer" : customerText;
    if(confirmPaymentMethod){
      confirmPaymentMethod.textContent = salePaymentMethod?.value === "online" ? "Online Cash" : "Counter Cash";
    }
    const data = getConfirmData();
    confirmItemCount.textContent = `${data.totalQty}`;
    confirmTotal.textContent = formatMoney(data.totalAmount);
    if(data.profitValid){
      confirmProfit.textContent = formatMoney(data.totalProfit);
    }else{
      confirmProfit.textContent = "N/A";
    }
    confirmProfit.classList.toggle("masked", Boolean(hideSalePrices));
    confirmProfitToggle?.classList.remove("is-shown");
    confirmProfitToggle?.setAttribute("aria-label", "Show profit");
    if(confirmProfitToggle){
      confirmProfitToggle.hidden = !hideSalePrices;
    }
    buildConfirmItems(data.items);
    if(confirmItemsList){
      confirmItemsList.setAttribute("hidden", "");
    }
  };

  const validateSaleForConfirmation = ()=>{
    const rows = saleEntryBody?.querySelectorAll("tr.sale-item-row") || [];
    if(!rows.length){
      showToast("Select at least one product to continue.", "error");
      return false;
    }
    for(const row of rows){
      const qtyInput = row.querySelector("input[name='sale_quantity[]']");
      const priceInput = row.querySelector("input[name='sale_price[]']");
      const productName = row.querySelector(".sale-item-name strong")?.textContent?.trim() || "Product";
      const qty = Number(qtyInput?.value || "");
      const price = Number(priceInput?.value || "");
      if(!Number.isFinite(qty) || qty <= 0){
        showToast(`Enter a valid quantity for ${productName}.`, "error");
        qtyInput?.focus();
        return false;
      }
      if(!Number.isFinite(price) || price < 0){
        showToast(`Enter a valid sale price for ${productName}.`, "error");
        priceInput?.focus();
        return false;
      }
    }
    return true;
  };

  const submitSaleForm = async ()=>{
    if(!saleForm){
      return;
    }
    confirmSaleSubmit.disabled = true;
    const formData = new FormData(saleForm);
    try{
      const response = await fetch(saleForm.action, {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const payload = await response.json();
      if(!response.ok || payload.status !== "ok"){
        showToast(payload.error || "Failed to record sale.", "error");
        confirmSaleSubmit.disabled = false;
        return;
      }
      resetSaleWorkflow();
      confirmSaleSubmit.disabled = false;
      showToast(payload.message || "Transaction saved successfully.", "success");
    }catch(err){
      showToast("Failed to record sale.", "error");
      confirmSaleSubmit.disabled = false;
    }
  };

  const openSaleConfirmation = ()=>{
    if(!saleForm){
      return;
    }
    if(!validateSaleForConfirmation()){
      return;
    }
    setConfirmData();
    openConfirmModal();
  };

  window.__openSaleConfirmation = openSaleConfirmation;

  saleForm?.addEventListener("submit", evt=>{
    evt.preventDefault();
    openSaleConfirmation();
  });

  openSaleConfirm?.addEventListener("click", ()=>{
    openSaleConfirmation();
  });

  confirmSaleSubmit?.addEventListener("click", async ()=>{
    await submitSaleForm();
  });

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

  const customerLookup = {{ customers|tojson }};

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
    openSaleDetailsModal();

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

  const walletHistoryDetailModal = document.getElementById("walletHistoryDetailModal");
  const walletHistoryDetailTitle = document.getElementById("walletHistoryDetailTitle");
  const walletHistoryDetailSub = document.getElementById("walletHistoryDetailSub");
  const walletHistoryDetailChannel = document.getElementById("walletHistoryDetailChannel");
  const walletHistoryDetailTotal = document.getElementById("walletHistoryDetailTotal");
  const walletHistoryDetailList = document.getElementById("walletHistoryDetailList");
  const expenseHistoryDetailModal = document.getElementById("expenseHistoryDetailModal");
  const expenseHistoryDetailTitle = document.getElementById("expenseHistoryDetailTitle");
  const expenseHistoryDetailSub = document.getElementById("expenseHistoryDetailSub");
  const expenseHistoryDetailTotal = document.getElementById("expenseHistoryDetailTotal");
  const expenseHistoryDetailList = document.getElementById("expenseHistoryDetailList");
  const expenseHistoryFilters = document.querySelectorAll("[data-cash-history-filter]");
  const cashSummaryFilterButtons = document.querySelectorAll("[data-cash-summary-filter]");
  const cashSummaryRows = document.querySelectorAll("[data-cash-summary-row]");
  const cashDetailFilterButtons = document.querySelectorAll("[data-cash-detail-filter]");
  const cashDetailRows = document.querySelectorAll("[data-cash-detail-row]");
  const paginatedHistorySections = ["allcash"];
  const cashSaleInfoModal = document.getElementById("cashSaleInfoModal");
  const cashSaleInfoTitle = document.getElementById("cashSaleInfoTitle");
  const cashSaleInfoSub = document.getElementById("cashSaleInfoSub");
  const cashSaleInfoCustomer = document.getElementById("cashSaleInfoCustomer");
  const cashSaleInfoTotal = document.getElementById("cashSaleInfoTotal");
  const cashSaleInfoProfit = document.getElementById("cashSaleInfoProfit");
  const cashSaleInfoProfitPercent = document.getElementById("cashSaleInfoProfitPercent");
  const cashSaleInfoItems = document.getElementById("cashSaleInfoItems");
  const cashRecordInfoModal = document.getElementById("cashRecordInfoModal");
  const cashRecordInfoTitle = document.getElementById("cashRecordInfoTitle");
  const cashRecordInfoSub = document.getElementById("cashRecordInfoSub");
  const cashRecordInfoChannel = document.getElementById("cashRecordInfoChannel");
  const cashRecordInfoType = document.getElementById("cashRecordInfoType");
  const cashRecordInfoAmount = document.getElementById("cashRecordInfoAmount");
  const cashRecordInfoTime = document.getElementById("cashRecordInfoTime");
  const cashRecordBalanceList = document.getElementById("cashRecordBalanceList");
  const cashRecordInfoMessage = document.getElementById("cashRecordInfoMessage");
  const cashRecordInfoActions = document.getElementById("cashRecordInfoActions");
  const walletHistoryTabButtons = document.querySelectorAll("[data-wallet-history-tab-target]");
  const walletHistoryPanels = document.querySelectorAll("[data-wallet-history-tab]");
  const openSystemCashModal = document.getElementById("openSystemCashModal");
  const openSystemCashQuickAction = document.getElementById("openSystemCashQuickAction");
  const openFinanceCashInModal = document.getElementById("openFinanceCashInModal");
  const openFinanceOutModal = document.getElementById("openFinanceOutModal");
  const financeModal = document.getElementById("financeModal");
  const financeModalTitle = document.getElementById("financeModalTitle");
  const financeModalSub = document.getElementById("financeModalSub");
  const financeModeInput = document.getElementById("financeModeInput");
  const financeModeField = document.getElementById("financeModeField");
  const financeCategory = document.getElementById("financeCategory");
  const financeCategoryField = document.getElementById("financeCategoryField");
  const financeEasyloadSourceField = document.getElementById("financeEasyloadSourceField");
  const financeEasyloadSource = document.getElementById("financeEasyloadSource");
  const financeSourceBalanceBadge = document.getElementById("financeSourceBalanceBadge");
  const financeSourceBalanceAmt = document.getElementById("financeSourceBalanceAmt");
  const financeInsufficientWarn = document.getElementById("financeInsufficientWarn");
  const financeInsufficientMsg = document.getElementById("financeInsufficientMsg");
  const financeNetworkField = document.getElementById("financeNetworkField");
  const financeNetwork = document.getElementById("financeNetwork");
  const financeChannelIcon = document.getElementById("financeChannelIcon");
  const financeAmountLabel = document.getElementById("financeAmountLabel");
  const financeAmountInput = document.getElementById("financeAmountInput");
  const financeNoteField = document.getElementById("financeNoteField");
  const financeNoteInput = document.getElementById("financeNoteInput");
  const financePreviewCard = document.getElementById("financePreviewCard");
  const financeRatePreview = document.getElementById("financeRatePreview");
  const financeProfitPreview = document.getElementById("financeProfitPreview");
  const financeSubmitBtn = document.getElementById("financeSubmitBtn");
  const financeCloseButtons = document.querySelectorAll("[data-finance-close]");
  const systemCashEntryType = document.getElementById("systemCashEntryType");
  const systemCashReason = document.getElementById("systemCashReason");
  const systemCashTypeIcon = document.getElementById("systemCashTypeIcon");
  const systemCashMessageLabel = document.getElementById("systemCashMessageLabel");
  const systemCashMessage = document.getElementById("systemCashMessage");
  const openWalletRefreshTrigger = document.getElementById("openWalletRefreshModal");
  const openEasyloadRefreshTrigger = document.getElementById("openEasyloadRefreshModal");
  const walletRefreshModal = document.getElementById("walletRefreshModal");
  const easyloadRefreshModal = document.getElementById("easyloadRefreshModal");
  const walletRefreshEasypaisa = document.getElementById("walletRefreshEasypaisa");
  const walletRefreshJazzcash = document.getElementById("walletRefreshJazzcash");
  const walletRefreshEasypaisaDiff = document.getElementById("walletRefreshEasypaisaDiff");
  const walletRefreshJazzcashDiff = document.getElementById("walletRefreshJazzcashDiff");
  const walletRefreshCloseButtons = document.querySelectorAll("[data-wallet-refresh-close]");
  const easyloadRefreshCloseButtons = document.querySelectorAll("[data-easyload-refresh-close]");
  const easyloadRefreshInputs = Array.from(document.querySelectorAll('[id^="easyloadRefresh"]')).filter(el=> el.tagName === "INPUT");
  const openWalletProfitTrigger = document.getElementById("openWalletProfitModal");
  const openPackageProfitTrigger = document.getElementById("openPackageProfitModal");
  const openEasyloadTrigger = document.getElementById("openEasyloadModal");
  const walletProfitChannel = document.getElementById("walletProfitChannel");
  const walletProfitChannelIcon = document.getElementById("walletProfitChannelIcon");
  const walletEntryType = document.getElementById("walletEntryType");
  const walletProfitDestination = document.getElementById("walletProfitDestination");
  const walletProfitAmountLabel = document.getElementById("walletProfitAmountLabel");
  const walletProfitAmountInput = document.getElementById("walletProfitAmountInput");
  const packageProfitEntryType = document.getElementById("packageProfitEntryType");
  const packageProfitReason = document.getElementById("packageProfitReason");
  const packageProfitMessageLabel = document.getElementById("packageProfitMessageLabel");
  const packageProfitAmountInput = document.getElementById("packageProfitAmountInput");
  const packageProfitNoteInput = document.getElementById("packageProfitNoteInput");
  const packageProfitSubmitBtn = document.getElementById("packageProfitSubmitBtn");
  const easyloadChannel = document.getElementById("easyloadChannel");
  const easyloadChannelIcon = document.getElementById("easyloadChannelIcon");
  const easyloadEntryType = document.getElementById("easyloadEntryType");
  const easyloadAmountInput = document.getElementById("easyloadAmountInput");
  const easyloadNoteField = document.getElementById("easyloadNoteField");
  const easyloadNoteInput = document.getElementById("easyloadNoteInput");
  const easyloadRatePreview = document.getElementById("easyloadRatePreview");
  const easyloadProfitPreview = document.getElementById("easyloadProfitPreview");
  const easyloadTotalPreview = document.getElementById("easyloadTotalPreview");
  const systemCashModal = document.getElementById("systemCashModal");
  const walletProfitModal = document.getElementById("walletProfitModal");
  const easyloadModal = document.getElementById("easyloadModal");
  const packageProfitModal = document.getElementById("packageProfitModal");
  const walletProfitCloseButtons = document.querySelectorAll("[data-wallet-profit-close]");
  const easyloadCloseButtons = document.querySelectorAll("[data-easyload-close]");
  const packageProfitCloseButtons = document.querySelectorAll("[data-package-profit-close]");
  const systemCashCloseButtons = document.querySelectorAll("[data-system-cash-close]");

  const profitChannelMeta = {
    easypaisa: {
      icon: "{{ url_for('static', filename='img/easypaisa-logo.png') }}",
      label: "Profit Amount",
      placeholder: "e.g. 50"
    },
    jazzcash: {
      icon: "{{ url_for('static', filename='img/jazzcash-logo.png') }}",
      label: "Profit Amount",
      placeholder: "e.g. 50"
    }
  };

  const easyloadRates = {
    zong: 24,
    jazz: 26,
    ufone: 20,
    telenor: 20
  };
  const easyloadLogos = {
    zong: "{{ url_for('static', filename='img/zong-logo.svg') }}",
    jazz: "{{ url_for('static', filename='img/jazz-warid-logo.svg') }}",
    ufone: "{{ url_for('static', filename='img/ufone-logo.svg') }}",
    telenor: "{{ url_for('static', filename='img/telenor-logo.svg') }}"
  };
  const financeCategoryLogos = {
    easypaisa: "{{ url_for('static', filename='img/easypaisa-logo.png') }}",
    jazzcash: "{{ url_for('static', filename='img/jazzcash-logo.png') }}"
  };

  const getFinanceCategoryLabel = ()=>{
    const selectedOption = financeCategory?.options?.[financeCategory.selectedIndex];
    return selectedOption?.textContent?.trim() || "wallet";
  };

  const getFinanceNetworkLabel = ()=>{
    const selectedOption = financeNetwork?.options?.[financeNetwork.selectedIndex];
    return selectedOption?.textContent?.trim() || "easyload";
  };

  const getEasyloadChannelLabel = ()=>{
    const selectedOption = easyloadChannel?.options?.[easyloadChannel.selectedIndex];
    return selectedOption?.textContent?.trim() || "easyload";
  };

  const getWalletCashInDefaultNote = ()=> `Cash transferred from counter to ${getFinanceCategoryLabel()}`;
  const getFinanceEasyloadDefaultNote = ()=>{
    const sourceVal = financeEasyloadSource?.value || "counter";
    if (sourceVal === "easypaisa") {
      return `Transferred from Easypaisa to ${getFinanceNetworkLabel()} easyload`;
    } else if (sourceVal === "jazzcash") {
      return `Transferred from JazzCash to ${getFinanceNetworkLabel()} easyload`;
    } else if (sourceVal === "online") {
      return `Transferred from online cash to ${getFinanceNetworkLabel()} easyload`;
    }
    return `Cash transferred from counter to ${getFinanceNetworkLabel()} easyload`;
  };
  const getEasyloadDefaultNote = ()=> `Cash transferred from counter to ${getEasyloadChannelLabel()} easyload`;
  const systemCashReasons = {
    add: [
      { value: "owner_added_cash", label: "Owner Added Cash", message: "Owner added cash to counter" },
      { value: "custom", label: "Custom", message: "" }
    ],
    expense: [
      { value: "shop_expense", label: "Shop Expense", message: "Shop expense paid from counter" },
      { value: "custom", label: "Custom", message: "" }
    ]
  };
  const walletProfitReasons = {
    wallet: [
      { value: "service_profit", label: "Service Profit", message: "Service profit added to wallet" },
      { value: "custom", label: "Custom", message: "" }
    ],
    counter: [
      { value: "profit_to_counter", label: "Profit to Counter", message: "Wallet profit moved to counter cash" },
      { value: "custom", label: "Custom", message: "" }
    ]
  };
  const packageProfitReasons = {
    profit_in: [
      { value: "package_profit", label: "Package Profit", message: "Package profit added" }
    ],
    profit_out: [
      { value: "mistake_reversal", label: "Mistake Reversal", message: "Package profit removed from counter cash" },
      { value: "custom", label: "Custom", message: "" }
    ]
  };

  const openWalletProfitModal = (modal)=>{
    if(!modal){
      return;
    }
    modal.classList.add("show");
  };

  const closeWalletProfitModal = (modal)=>{
    modal?.classList.remove("show");
  };

  const walletRefreshDifferenceText = (input, output)=>{
    if(!input || !output){
      return;
    }
    const actual = Number(input.value || 0);
    const current = Number(input.dataset.current || 0);
    const diff = Number.isFinite(actual) ? actual - current : 0;
    const sign = diff < 0 ? "-" : "+";
    output.classList.toggle("is-out", diff < 0);
    output.classList.toggle("is-in", diff > 0);
    output.textContent = `Difference: ${sign}${formatMoney(Math.abs(diff))}`;
  };

  const syncWalletRefreshPreview = ()=>{
    walletRefreshDifferenceText(walletRefreshEasypaisa, walletRefreshEasypaisaDiff);
    walletRefreshDifferenceText(walletRefreshJazzcash, walletRefreshJazzcashDiff);
  };

  const resetWalletRefreshForm = ()=>{
    [walletRefreshEasypaisa, walletRefreshJazzcash].forEach(input=>{
      if(input){
        input.value = Number(input.dataset.current || 0).toFixed(2);
      }
    });
    syncWalletRefreshPreview();
  };

  const syncEasyloadRefreshPreview = ()=>{
    easyloadRefreshInputs.forEach(input=>{
      const diffOutput = document.getElementById(`${input.id}Diff`);
      walletRefreshDifferenceText(input, diffOutput);
    });
  };

  const resetEasyloadRefreshForm = ()=>{
    easyloadRefreshInputs.forEach(input=>{
      input.value = Number(input.dataset.current || 0).toFixed(2);
    });
    syncEasyloadRefreshPreview();
  };

  const syncFinanceModal = ()=>{
    if(!financeModeInput || !financeCategory){
      return;
    }
    const mode = financeModeInput.value || "cash_in";
    const category = financeCategory.value || "easypaisa";
    const isEasyload = category === "easyload";
    const hasDefaultCashInNote = mode === "cash_in";
    const network = financeNetwork?.value || "zong";
    const rate = Number(easyloadRates[network] || 0);
    const amount = Number(financeAmountInput?.value || 1000);
    const safeAmount = Number.isFinite(amount) && amount > 0 ? amount : 0;
    const expectedProfit = mode === "cash_in" && isEasyload ? (safeAmount / 1000) * rate : 0;

    if (financeModeField) {
      financeModeField.hidden = isEasyload;
    }
    if (financeCategoryField) {
      financeCategoryField.hidden = isEasyload;
    }
    if (financeEasyloadSourceField) {
      financeEasyloadSourceField.hidden = !isEasyload;
    }

    if(financeModalTitle){
      financeModalTitle.textContent = isEasyload ? "Recharge Easyload" : (mode === "cash_in" ? "Cash In" : "Out");
    }
    if(financeModalSub){
      financeModalSub.textContent = isEasyload
        ? "Add new network load balance from a mobile wallet or counter cash."
        : (mode === "cash_in"
          ? "Choose Easypaisa, JazzCash, or All Network Load for cash in."
          : "Choose Easypaisa, JazzCash, or All Network Load for out.");
    }
    if(financeNetworkField){
      financeNetworkField.hidden = !isEasyload;
    }
    if(financeAmountLabel){
      financeAmountLabel.textContent = isEasyload ? "Recharge Amount" : "Amount";
    }
    if(financeAmountInput){
      financeAmountInput.placeholder = isEasyload ? "e.g. 1000" : "e.g. 5000";
    }
    if(financeNoteField){
      financeNoteField.hidden = hasDefaultCashInNote;
    }
    if(financeNoteInput){
      financeNoteInput.required = !hasDefaultCashInNote;
      if(hasDefaultCashInNote){
        const defaultNote = isEasyload ? getFinanceEasyloadDefaultNote() : getWalletCashInDefaultNote();
        financeNoteInput.value = defaultNote;
        financeNoteInput.dataset.autoDefault = "cash-in";
        financeNoteInput.placeholder = defaultNote;
      }else if(financeNoteInput.dataset.autoDefault === "cash-in"){
        financeNoteInput.value = "";
        delete financeNoteInput.dataset.autoDefault;
      }
      if(isEasyload){
        financeNoteInput.placeholder = "e.g. Purchased network balance";
      }else{
        financeNoteInput.placeholder = mode === "cash_in"
          ? "e.g. Cash received from customer"
          : "e.g. Sent amount to customer";
      }
    }
    if(financePreviewCard){
      financePreviewCard.hidden = !isEasyload;
    }
    if(financeChannelIcon){
      financeChannelIcon.src = isEasyload
        ? (easyloadLogos[network] || easyloadLogos.zong)
        : (financeCategoryLogos[category] || financeCategoryLogos.easypaisa);
    }
    if(financeRatePreview){
      financeRatePreview.textContent = `PKR ${rate.toFixed(2)} / 1000`;
    }
    if(financeProfitPreview){
      financeProfitPreview.textContent = `PKR ${expectedProfit.toFixed(2)}`;
    }
    if(financeSubmitBtn){
      financeSubmitBtn.textContent = isEasyload ? "Confirm Recharge" : (mode === "cash_in" ? "Save Cash In" : "Save Out");
    }

    // --- Balance validation for Easyload recharge ---
    if(isEasyload && financeEasyloadSource){
      const sourceVal = financeEasyloadSource.value || "counter";
      const modalEl = document.getElementById("financeModal");
      const balances = {
        counter:   Number(modalEl?.dataset.balCounter  || 0),
        online:    Number(modalEl?.dataset.balOnline   || 0),
        easypaisa: Number(modalEl?.dataset.balEasypaisa|| 0),
        jazzcash:  Number(modalEl?.dataset.balJazzcash || 0),
      };
      const sourceBal = balances[sourceVal] ?? 0;
      const sourceLabels = {
        counter:   "Counter Cash",
        online:    "Online Cash",
        easypaisa: "Easypaisa Wallet",
        jazzcash:  "JazzCash Wallet",
      };
      if(financeSourceBalanceAmt){
        financeSourceBalanceAmt.textContent = `PKR ${sourceBal.toLocaleString("en-PK", {minimumFractionDigits:2, maximumFractionDigits:2})}`;
        financeSourceBalanceAmt.style.color = sourceBal > 0 ? "#4ade80" : "#f87171";
      }
      const enteredAmt = Number(financeAmountInput?.value || 0);
      const isInsufficient = enteredAmt > 0 && enteredAmt > sourceBal;
      if(financeInsufficientWarn){
        financeInsufficientWarn.hidden = !isInsufficient;
        financeInsufficientWarn.style.display = isInsufficient ? "flex" : "none";
      }
      if(financeInsufficientMsg && isInsufficient){
        financeInsufficientMsg.textContent = `${sourceLabels[sourceVal]} only has PKR ${sourceBal.toFixed(2)} available. Reduce the amount to proceed.`;
      }
      if(financeSubmitBtn){
        financeSubmitBtn.disabled = isInsufficient;
        financeSubmitBtn.style.opacity = isInsufficient ? "0.45" : "";
        financeSubmitBtn.style.cursor  = isInsufficient ? "not-allowed" : "";
      }
    } else {
      // Reset validation state for non-easyload mode
      if(financeInsufficientWarn){ financeInsufficientWarn.hidden = true; financeInsufficientWarn.style.display = "none"; }
      if(financeSubmitBtn){ financeSubmitBtn.disabled = false; financeSubmitBtn.style.opacity = ""; financeSubmitBtn.style.cursor = ""; }
    }
  };

  const openWalletHistoryDetailModal = ({ channel, day, total, entries, title, totalLabel })=>{
    if(!walletHistoryDetailModal || !walletHistoryDetailList){
      return;
    }
    const safeEntries = Array.isArray(entries) ? entries : [];
    if(walletHistoryDetailTitle){
      walletHistoryDetailTitle.textContent = title || `${channel} activity`;
    }
    if(walletHistoryDetailSub){
      walletHistoryDetailSub.textContent = `${day} | ${safeEntries.length} entr${safeEntries.length === 1 ? "y" : "ies"}`;
    }
    if(walletHistoryDetailChannel){
      walletHistoryDetailChannel.textContent = channel;
    }
    if(walletHistoryDetailTotal){
      walletHistoryDetailTotal.textContent = totalLabel || `PKR ${total}`;
    }

    const hasProfitColumn = safeEntries.some(e => e && e.profit_amount !== undefined && e.profit_amount !== null);
    const profitHeader = document.getElementById("walletHistoryDetailProfitHeader");
    if(profitHeader){
      profitHeader.style.display = hasProfitColumn ? "" : "none";
    }

    walletHistoryDetailList.innerHTML = "";
    safeEntries.forEach((entry, index)=>{
      if(!entry) return;
      const tr = document.createElement("tr");

      // 1. Sr.
      const tdSr = document.createElement("td");
      tdSr.className = "product-sr-cell";
      tdSr.textContent = index + 1;

      // 2. Time
      const tdTime = document.createElement("td");
      const parsed = entry.created_at ? new Date(String(entry.created_at).replace(" ", "T")) : null;
      const timeLabel = parsed && !Number.isNaN(parsed.getTime())
        ? parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", hour12: true })
        : (entry.created_at || "");
      tdTime.textContent = timeLabel;

      // 3. Details
      const tdDetails = document.createElement("td");
      const labelSpan = document.createElement("strong");
      labelSpan.style.color = "#fff";
      labelSpan.style.display = "block";
      labelSpan.textContent = entry.entry_label || "";
      const noteSpan = document.createElement("span");
      noteSpan.className = "muted";
      noteSpan.style.fontSize = "11px";
      noteSpan.textContent = entry.note || "";
      tdDetails.append(labelSpan, noteSpan);

      // 4. Amount
      const tdAmount = document.createElement("td");
      tdAmount.style.textAlign = "right";
      tdAmount.textContent = `PKR ${Number(entry.amount || 0).toFixed(2)}`;

      tr.append(tdSr, tdTime, tdDetails, tdAmount);

      // 5. Profit
      if(hasProfitColumn){
        const tdProfit = document.createElement("td");
        tdProfit.style.textAlign = "right";
        tdProfit.style.fontWeight = "bold";
        tdProfit.style.color = "var(--accent-2, #38bdf8)";
        if(entry.profit_amount !== undefined && entry.profit_amount !== null){
          tdProfit.textContent = `PKR ${Number(entry.profit_amount || 0).toFixed(2)}`;
        } else {
          tdProfit.textContent = "-";
        }
        tr.append(tdProfit);
      }

      walletHistoryDetailList.append(tr);
    });

    if(!safeEntries.length){
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = hasProfitColumn ? 5 : 4;
      td.style.textAlign = "center";
      td.style.padding = "24px";
      td.className = "muted";
      td.textContent = "No entries found for this date.";
      tr.append(td);
      walletHistoryDetailList.append(tr);
    }

    walletHistoryDetailModal.classList.add("show");
  };

  let currentCashHistoryEntries = [];
  let currentCashHistoryFilter = "all";
  let currentCashSummaryFilter = "all";
  let currentCashDetailFilter = "all";
  const historyPageSize = 10;
  const historyPaginationState = {
    allcash: 1,
  };
  const isSaleCashEntry = entry => /Sale(?: received| restored)? #\d+/i.test(String(entry?.note || entry?.expense_name || ""));

  const cashRecordTimeLabel = entry=>{
    const parsed = entry?.created_at ? new Date(String(entry.created_at).replace(" ", "T")) : null;
    return parsed && !Number.isNaN(parsed.getTime())
      ? parsed.toLocaleString([], { hour: "numeric", minute: "2-digit", hour12: true, year: "numeric", month: "short", day: "numeric" })
      : (entry?.created_at || entry?.timestamp || "-");
  };

  const openCashRecordInfoModal = entry=>{
    if(!cashRecordInfoModal){
      return;
    }
    const record = entry || {};
    const noteText = String(record.note || record.expense_name || "-");
    const isWalletBalanceUpdate = noteText.toLowerCase().startsWith("wallet balance updated:");
    const displayMessage = isWalletBalanceUpdate ? "Wallet balance updated" : noteText;
    const signedAmount = Number(record.signed_amount ?? record.amount ?? 0);
    const amountLabel = record.detail_kind === "wallet_profit_transfer"
      ? formatMoney(Number(record.amount || 0))
      : `${signedAmount < 0 ? "-" : signedAmount > 0 ? "+" : ""}${formatMoney(Math.abs(signedAmount || Number(record.amount || 0)))}`;
    const sourceLabel = isWalletBalanceUpdate ? "Wallet balance" : [record.source, record.meta].filter(Boolean).join(" | ");
    const saleMatch = noteText.match(/Sale(?: received| restored)? #(\d+)/i);

    if(cashRecordInfoTitle){
      cashRecordInfoTitle.textContent = record.entry_label || "Cash Record Details";
    }
    if(cashRecordInfoSub){
      cashRecordInfoSub.textContent = sourceLabel || "Cash movement";
    }
    if(cashRecordInfoChannel){
      cashRecordInfoChannel.textContent = record.channel_label || record.source || "-";
    }
    if(cashRecordInfoType){
      cashRecordInfoType.textContent = record.entry_label || "-";
    }
    if(cashRecordInfoAmount){
      cashRecordInfoAmount.textContent = amountLabel;
    }
    if(cashRecordInfoTime){
      cashRecordInfoTime.textContent = cashRecordTimeLabel(record);
    }
    if(cashRecordInfoMessage){
      cashRecordInfoMessage.textContent = displayMessage;
    }
    if(cashRecordBalanceList){
      cashRecordBalanceList.innerHTML = "";
      const changes = Array.isArray(record.balance_changes) ? record.balance_changes : [];
      changes.forEach(change=>{
        const item = document.createElement("div");
        item.className = "cash-record-balance-item";

        const label = document.createElement("strong");
        label.textContent = change.label || "Cash";

        const values = document.createElement("div");
        values.className = "cash-record-balance-values";
        values.innerHTML = `
          <span><small>Before</small>${formatMoney(Number(change.before || 0))}</span>
          <span><small>After</small>${formatMoney(Number(change.after || 0))}</span>
        `;

        const delta = document.createElement("em");
        const deltaValue = Number(change.delta || 0);
        delta.className = deltaValue < 0 ? "is-out" : "is-in";
        delta.textContent = `${deltaValue < 0 ? "-" : "+"}${formatMoney(Math.abs(deltaValue))}`;

        item.append(label, values, delta);
        cashRecordBalanceList.append(item);
      });
      if(!changes.length){
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "No balance movement was recorded for this entry.";
        cashRecordBalanceList.append(empty);
      }
    }
    if(cashRecordInfoActions){
      cashRecordInfoActions.innerHTML = "";
      if(saleMatch && record.detail_kind === "counter"){
        const saleButton = document.createElement("button");
        saleButton.type = "button";
        saleButton.className = "btn btn-secondary btn-mini";
        saleButton.textContent = `View Sale #${saleMatch[1]}`;
        saleButton.addEventListener("click", ()=> openCashSaleInfoModal(saleMatch[1]));
        cashRecordInfoActions.append(saleButton);
      }
    }
    cashRecordInfoModal.classList.add("show");
  };

  const renderExpenseHistoryDetailEntries = ()=>{
    if(!expenseHistoryDetailList){
      return;
    }
    const entries = currentCashHistoryEntries.filter(entry=>{
      if(currentCashHistoryFilter === "all"){
        return true;
      }
      const tags = Array.isArray(entry?.filter_tags) ? entry.filter_tags : [entry?.bucket || "other"];
      return tags.includes(currentCashHistoryFilter);
    });

    expenseHistoryDetailList.innerHTML = "";
    entries.forEach((entry, index)=>{
      const row = document.createElement("div");
      row.className = "wallet-history-detail-item cash-history-detail-item";

      const sr = document.createElement("span");
      sr.className = "cash-history-cell cash-history-sr";
      sr.textContent = `${index + 1}.`;

      const type = document.createElement("span");
      const isOut = Number(entry.signed_amount ?? 0) < 0 || entry.entry_type === "expense" || entry.entry_type === "cash_out" || entry.entry_type === "out";
      type.className = `cash-entry-type cash-history-cell ${isOut ? "is-out" : "is-in"}`;
      type.textContent = entry.entry_label || (isOut ? "Cash Out" : "Cash In");

      const meta = document.createElement("small");
      meta.className = "cash-history-cell cash-history-time";
      const parsed = entry.created_at ? new Date(String(entry.created_at).replace(" ", "T")) : null;
      const timeLabel = parsed && !Number.isNaN(parsed.getTime())
        ? parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", hour12: true })
        : (entry.created_at || "");
      const sourceLabel = [entry.source, entry.channel_label, entry.meta].filter(Boolean).join(" | ");
      meta.textContent = [timeLabel, sourceLabel].filter(Boolean).join(" | ");

      const impact = document.createElement("div");
      impact.className = "cash-history-impact-list";
      const changes = Array.isArray(entry.balance_changes) ? entry.balance_changes : [];
      changes.forEach(change=>{
        const chip = document.createElement("span");
        const deltaValue = Number(change.delta || 0);
        chip.className = `cash-impact-pill ${deltaValue < 0 ? "is-out" : "is-in"}`;
        chip.textContent = `${change.label || "Cash"} ${deltaValue < 0 ? "-" : "+"}PKR ${Math.abs(deltaValue).toFixed(2)}`;
        impact.append(chip);
      });
      if(!changes.length){
        const emptyImpact = document.createElement("span");
        emptyImpact.className = "muted";
        emptyImpact.textContent = "-";
        impact.append(emptyImpact);
      }

      const infoButton = document.createElement("button");
      infoButton.type = "button";
      infoButton.className = "cash-history-info-btn";
      infoButton.textContent = "i";
      infoButton.setAttribute("aria-label", `View ${entry.entry_label || "cash record"} details`);
      infoButton.addEventListener("click", ()=> openCashRecordInfoModal(entry));

      row.append(sr, type, meta, impact, infoButton);
      expenseHistoryDetailList.append(row);
    });
    if(!entries.length){
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = currentCashHistoryFilter === "all"
        ? "No cash entries found for this date."
        : `No ${currentCashHistoryFilter} entries found for this date.`;
      expenseHistoryDetailList.append(empty);
    }
  };

  const openExpenseHistoryDetailModal = ({ day, total, entries })=>{
    if(!expenseHistoryDetailModal || !expenseHistoryDetailList){
      return;
    }
    if(expenseHistoryDetailTitle){
      expenseHistoryDetailTitle.textContent = "Cash activity";
    }
    if(expenseHistoryDetailSub){
      expenseHistoryDetailSub.textContent = `${day} • ${entries.length} entr${entries.length === 1 ? "y" : "ies"}`;
    }
    if(expenseHistoryDetailTotal){
      expenseHistoryDetailTotal.textContent = `PKR ${total}`;
    }
    currentCashHistoryEntries = Array.isArray(entries) ? entries : [];
    currentCashHistoryFilter = "all";
    expenseHistoryFilters.forEach(btn=>{
      btn.classList.toggle("active", btn.dataset.cashHistoryFilter === "all");
    });
    renderExpenseHistoryDetailEntries();
    expenseHistoryDetailModal.classList.add("show");
  };

  const openCashSaleInfoModal = async saleId=>{
    if(!cashSaleInfoModal || !cashSaleInfoItems){
      return;
    }
    if(cashSaleInfoTitle){
      cashSaleInfoTitle.textContent = `Sale #${saleId}`;
    }
    if(cashSaleInfoSub){
      cashSaleInfoSub.textContent = "Loading sale details...";
    }
    if(cashSaleInfoCustomer){
      cashSaleInfoCustomer.textContent = "-";
    }
    if(cashSaleInfoTotal){
      cashSaleInfoTotal.textContent = "PKR 0.00";
    }
    if(cashSaleInfoProfit){
      cashSaleInfoProfit.textContent = "PKR 0.00";
    }
    if(cashSaleInfoProfitPercent){
      cashSaleInfoProfitPercent.textContent = "-";
    }
    cashSaleInfoItems.innerHTML = `<tr><td colspan="8" class="muted">Loading sale details...</td></tr>`;
    cashSaleInfoModal.classList.add("show");

    try{
      const response = await fetch(`/manager/sales/${saleId}/cash-summary`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      const data = await response.json();
      if(!response.ok || data.status !== "ok" || !data.sale){
        throw new Error(data.error || "Failed to load sale details.");
      }

      const sale = data.sale;
      if(cashSaleInfoTitle){
        cashSaleInfoTitle.textContent = `Sale #${sale.sale_id}`;
      }
      if(cashSaleInfoSub){
        cashSaleInfoSub.textContent = sale.created_at || "Sale details";
      }
      if(cashSaleInfoCustomer){
        cashSaleInfoCustomer.textContent = sale.customer_name || "Walk-in Customer";
      }
      if(cashSaleInfoTotal){
        cashSaleInfoTotal.textContent = `PKR ${Number(sale.sale_total || 0).toFixed(2)}`;
      }
      if(cashSaleInfoProfit){
        cashSaleInfoProfit.textContent = `PKR ${Number(sale.profit || 0).toFixed(2)}`;
      }
      if(cashSaleInfoProfitPercent){
        cashSaleInfoProfitPercent.textContent = sale.profit_percent == null ? "-" : `${Number(sale.profit_percent).toFixed(2)}%`;
      }
      cashSaleInfoItems.innerHTML = "";
      (sale.items || []).forEach((item, index)=>{
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${index + 1}</td>
          <td>${item.product_name || "-"}</td>
          <td>${item.quantity || 0}</td>
          <td>PKR ${Number(item.purchase_rate || 0).toFixed(2)}</td>
          <td>PKR ${Number(item.sale_price || 0).toFixed(2)}</td>
          <td>PKR ${Number(item.line_total || 0).toFixed(2)}</td>
          <td>PKR ${Number(item.profit || 0).toFixed(2)}</td>
          <td>${item.profit_percent == null ? "-" : `${Number(item.profit_percent).toFixed(2)}%`}</td>
        `;
        cashSaleInfoItems.append(tr);
      });
      if(!(sale.items || []).length){
        cashSaleInfoItems.innerHTML = `<tr><td colspan="8" class="muted">No sale items found.</td></tr>`;
      }
    } catch (error){
      if(cashSaleInfoSub){
        cashSaleInfoSub.textContent = error.message || "Failed to load sale details.";
      }
      cashSaleInfoItems.innerHTML = `<tr><td colspan="8" class="muted">Unable to load sale details right now.</td></tr>`;
    }
  };

  const syncWalletChannelIcon = ()=>{
    if(!walletProfitChannel || !walletProfitChannelIcon){
      return;
    }
    const meta = profitChannelMeta[walletProfitChannel.value] || profitChannelMeta.easypaisa;
    if(meta.icon){
      walletProfitChannelIcon.src = meta.icon;
      walletProfitChannelIcon.style.visibility = "visible";
    }else{
      walletProfitChannelIcon.removeAttribute("src");
      walletProfitChannelIcon.style.visibility = "hidden";
    }
    if(walletProfitAmountLabel){
      walletProfitAmountLabel.textContent = "Profit Amount";
    }
    if(walletProfitAmountInput){
      walletProfitAmountInput.placeholder = "e.g. 250";
    }
  };

  const syncPackageProfitReasonMessage = ()=>{
    if(!packageProfitReason || !packageProfitNoteInput || !packageProfitEntryType){
      return;
    }
    const reasons = packageProfitReasons[packageProfitEntryType.value] || packageProfitReasons.profit_in;
    const selectedReason = reasons.find(reason=> reason.value === packageProfitReason.value) || reasons[0];
    if(selectedReason.value === "custom"){
      if(packageProfitNoteInput.dataset.autoReason === "1"){
        packageProfitNoteInput.value = "";
      }
      packageProfitNoteInput.readOnly = false;
      packageProfitNoteInput.placeholder = packageProfitEntryType.value === "profit_out"
        ? "e.g. Wrong package profit entry reversed"
        : "e.g. Package commission received";
      delete packageProfitNoteInput.dataset.autoReason;
      return;
    }
    packageProfitNoteInput.value = selectedReason.message;
    packageProfitNoteInput.readOnly = true;
    packageProfitNoteInput.placeholder = selectedReason.message;
    packageProfitNoteInput.dataset.autoReason = "1";
  };

  const syncPackageProfitForm = ()=>{
    if(!packageProfitEntryType){
      return;
    }
    const isProfitOut = packageProfitEntryType.value === "profit_out";
    if(packageProfitMessageLabel){
      packageProfitMessageLabel.textContent = isProfitOut ? "Profit Out Message" : "Profit In Message";
    }
    if(packageProfitAmountInput){
      packageProfitAmountInput.placeholder = isProfitOut ? "e.g. 500" : "e.g. 500";
    }
    if(packageProfitReason){
      const reasons = packageProfitReasons[packageProfitEntryType.value] || packageProfitReasons.profit_in;
      packageProfitReason.innerHTML = "";
      reasons.forEach(reason=>{
        const option = document.createElement("option");
        option.value = reason.value;
        option.textContent = reason.label;
        packageProfitReason.append(option);
      });
    }
    if(packageProfitSubmitBtn){
      packageProfitSubmitBtn.textContent = isProfitOut ? "Save Profit Out" : "Save Profit In";
    }
    syncPackageProfitReasonMessage();
  };

  const syncCashSummaryHistory = ()=>{
    if(!cashSummaryRows.length){
      return;
    }
    cashSummaryRows.forEach(row=>{
      const buckets = String(row.dataset.cashSummaryBuckets || "")
        .split(",")
        .map(item=> item.trim())
        .filter(Boolean);
      const show = currentCashSummaryFilter === "all" || buckets.includes(currentCashSummaryFilter);
      row.hidden = !show;
    });
  };

  const syncCashDetailHistory = ()=>{
    if(!cashDetailRows.length){
      return;
    }
    cashDetailRows.forEach(row=>{
      const bucket = row.dataset.cashDetailBucket || "counter";
      const show = currentCashDetailFilter === "all" || bucket === currentCashDetailFilter;
      row.hidden = !show;
    });
  };

  const syncPaginatedHistoryTable = section=>{
    const rows = Array.from(document.querySelectorAll(`[data-history-row="${section}"]`));
    if(!rows.length){
      return;
    }
    const page = historyPaginationState[section] || 1;
    const total = rows.length;
    const totalPages = Math.max(1, Math.ceil(total / historyPageSize));
    const safePage = Math.min(page, totalPages);
    historyPaginationState[section] = safePage;
    const start = (safePage - 1) * historyPageSize;
    const end = start + historyPageSize;
    rows.forEach((row, index)=>{
      const visible = index >= start && index < end;
      row.hidden = !visible;
      const srCell = row.querySelector("[data-history-sr]");
      if(visible && srCell){
        srCell.textContent = `${index + 1}`;
      }
    });
    const meta = document.querySelector(`[data-history-meta="${section}"]`);
    if(meta){
      meta.textContent = total ? `Showing ${start + 1}-${Math.min(end, total)} of ${total} | Page ${safePage} of ${totalPages}` : "Page 0 of 0";
    }
    const prevBtn = document.querySelector(`[data-history-prev="${section}"]`);
    if(prevBtn){
      prevBtn.disabled = safePage <= 1;
    }
    const nextBtn = document.querySelector(`[data-history-next="${section}"]`);
    if(nextBtn){
      nextBtn.disabled = safePage >= totalPages;
    }
    const pager = document.querySelector(`[data-history-pagination="${section}"]`);
    if(pager){
      pager.hidden = total <= historyPageSize;
    }
  };

  const syncEasyloadPreview = ()=>{
    if(!easyloadChannel){
      return;
    }
    if(easyloadChannelIcon){
      easyloadChannelIcon.src = easyloadLogos[easyloadChannel.value] || easyloadLogos.zong;
    }
    const rate = Number(easyloadRates[easyloadChannel.value] || 0);
    const loadAmount = Number(easyloadAmountInput?.value || 1000);
    const safeLoadAmount = Number.isFinite(loadAmount) && loadAmount > 0 ? loadAmount : 0;
    const isPurchaseIn = (easyloadEntryType?.value || "purchase_in") === "purchase_in";
    const profitAmount = isPurchaseIn ? (safeLoadAmount / 1000) * rate : 0;
    const totalAmount = safeLoadAmount;
    if(easyloadRatePreview){
      easyloadRatePreview.textContent = `PKR ${rate.toFixed(2)} / 1000`;
    }
    if(easyloadProfitPreview){
      easyloadProfitPreview.textContent = `PKR ${profitAmount.toFixed(2)}`;
    }
    if(easyloadTotalPreview){
      easyloadTotalPreview.textContent = `PKR ${totalAmount.toFixed(2)}`;
    }
    if(easyloadNoteField){
      easyloadNoteField.hidden = isPurchaseIn;
    }
    if(easyloadNoteInput){
      easyloadNoteInput.required = !isPurchaseIn;
      if(isPurchaseIn){
        const defaultNote = getEasyloadDefaultNote();
        easyloadNoteInput.value = defaultNote;
        easyloadNoteInput.dataset.autoDefault = "purchase-in";
        easyloadNoteInput.placeholder = defaultNote;
      }else{
        if(easyloadNoteInput.dataset.autoDefault === "purchase-in"){
          easyloadNoteInput.value = "";
          delete easyloadNoteInput.dataset.autoDefault;
        }
        easyloadNoteInput.placeholder = "e.g. Sold load to customer";
      }
    }
  };

  const syncSystemCashReasonMessage = ()=>{
    if(!systemCashReason || !systemCashMessage || !systemCashEntryType){
      return;
    }
    const reasons = systemCashReasons[systemCashEntryType.value] || systemCashReasons.add;
    const selectedReason = reasons.find(reason=> reason.value === systemCashReason.value) || reasons[0];
    if(selectedReason.value === "custom"){
      if(systemCashMessage.dataset.autoReason === "1"){
        systemCashMessage.value = "";
      }
      systemCashMessage.readOnly = false;
      systemCashMessage.placeholder = systemCashEntryType.value === "expense"
        ? "e.g. Paid shop expense"
        : "e.g. Owner added cash";
      delete systemCashMessage.dataset.autoReason;
      return;
    }
    systemCashMessage.value = selectedReason.message;
    systemCashMessage.readOnly = true;
    systemCashMessage.placeholder = selectedReason.message;
    systemCashMessage.dataset.autoReason = "1";
  };

  const syncSystemCashTypeIcon = ()=>{
    if(!systemCashEntryType || !systemCashTypeIcon){
      return;
    }
    const isCashOut = systemCashEntryType.value === "expense";
    systemCashTypeIcon.classList.toggle("cash-flow-in", !isCashOut);
    systemCashTypeIcon.classList.toggle("cash-flow-out", isCashOut);
    if(systemCashMessageLabel){
      systemCashMessageLabel.textContent = isCashOut ? "Cash Out Message" : "Cash In Message";
    }
    if(systemCashReason){
      const reasons = systemCashReasons[systemCashEntryType.value] || systemCashReasons.add;
      systemCashReason.innerHTML = "";
      reasons.forEach(reason=>{
        const option = document.createElement("option");
        option.value = reason.value;
        option.textContent = reason.label;
        systemCashReason.append(option);
      });
    }
    if(systemCashMessage){
      systemCashMessage.placeholder = isCashOut
        ? "Shop expense paid from counter"
        : "Owner added cash to counter";
    }
    syncSystemCashReasonMessage();
  };

  const activateWalletHistoryTab = tabKey=>{
    walletHistoryTabButtons.forEach(btn=>{
      const active = btn.dataset.walletHistoryTabTarget === tabKey;
      btn.classList.toggle("active", active);
    });
    walletHistoryPanels.forEach(panel=>{
      panel.hidden = panel.dataset.walletHistoryTab !== tabKey;
    });
  };

  [systemCashModal, walletProfitModal, easyloadModal, financeModal, packageProfitModal].forEach(modal=>{
    if(!modal){
      return;
    }
    modal.addEventListener("click", evt=>{
      if(evt.target === modal){
        closeWalletProfitModal(modal);
      }
    });
  });

  openSystemCashModal?.addEventListener("click", ()=>{
    syncSystemCashTypeIcon();
    openWalletProfitModal(systemCashModal);
  });
  openSystemCashQuickAction?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    syncSystemCashTypeIcon();
    openWalletProfitModal(systemCashModal);
  });

  // ── Cash Transfer Modal ──────────────────────────────────────────────
  const cashTransferModal        = document.getElementById("cashTransferModal");
  const cashTransferSource       = document.getElementById("cashTransferSource");
  const cashTransferTarget       = document.getElementById("cashTransferTarget");
  const cashTransferAmount       = document.getElementById("cashTransferAmount");
  const cashTransferNote         = document.getElementById("cashTransferNote");
  const cashTransferSourceBal    = document.getElementById("cashTransferSourceBal");
  const cashTransferInsufficientWarn = document.getElementById("cashTransferInsufficientWarn");
  const cashTransferInsufficientMsg  = document.getElementById("cashTransferInsufficientMsg");
  const cashTransferSubmitBtn    = document.getElementById("cashTransferSubmitBtn");

  const TRANSFER_SOURCE_LABELS = {
    counter:   "Counter Cash",
    online:    "Online Cash",
    easypaisa: "Easypaisa Wallet",
    jazzcash:  "JazzCash Wallet",
  };

  const getCashTransferBalances = ()=>{
    const el = cashTransferModal;
    return {
      counter:   Number(el?.dataset.balCounter   || 0),
      online:    Number(el?.dataset.balOnline     || 0),
      easypaisa: Number(el?.dataset.balEasypaisa  || 0),
      jazzcash:  Number(el?.dataset.balJazzcash   || 0),
    };
  };

  const syncCashTransfer = ()=>{
    const src = cashTransferSource?.value || "counter";
    const balances = getCashTransferBalances();
    const srcBal = balances[src] ?? 0;

    // Update source balance badge
    if(cashTransferSourceBal){
      cashTransferSourceBal.textContent = `PKR ${srcBal.toLocaleString("en-PK", {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      cashTransferSourceBal.style.color = srcBal > 0 ? "#4ade80" : "#f87171";
    }

    // Filter target to exclude same as source
    if(cashTransferTarget){
      Array.from(cashTransferTarget.options).forEach(opt=>{
        opt.hidden = opt.value === src;
      });
      if(cashTransferTarget.value === src){
        const first = Array.from(cashTransferTarget.options).find(o => o.value !== src);
        if(first) cashTransferTarget.value = first.value;
      }
    }

    // Amount validation
    const entered = Number(cashTransferAmount?.value || 0);
    const isInsufficient = entered > 0 && entered > srcBal;
    if(cashTransferInsufficientWarn){
      cashTransferInsufficientWarn.hidden = !isInsufficient;
      cashTransferInsufficientWarn.style.display = isInsufficient ? "flex" : "none";
    }
    if(cashTransferInsufficientMsg && isInsufficient){
      cashTransferInsufficientMsg.textContent =
        `${TRANSFER_SOURCE_LABELS[src] || src} only has PKR ${srcBal.toFixed(2)} available.`;
    }
    if(cashTransferSubmitBtn){
      cashTransferSubmitBtn.disabled = isInsufficient;
      cashTransferSubmitBtn.style.opacity = isInsufficient ? "0.45" : "";
      cashTransferSubmitBtn.style.cursor  = isInsufficient ? "not-allowed" : "";
    }

    // Auto-generate note
    if(cashTransferNote && !cashTransferNote.value){
      const tgt = cashTransferTarget?.value || "online";
      cashTransferNote.placeholder = `Transfer from ${TRANSFER_SOURCE_LABELS[src]||src} to ${TRANSFER_SOURCE_LABELS[tgt]||tgt}`;
    }
  };

  // Open trigger (from quick-action card)
  document.addEventListener("click", evt=>{
    if(evt.target.closest("[data-trigger-btn='openCashTransferModal']")){
      setQuickActionsOpen(false);
      // reset form
      if(cashTransferSource)  cashTransferSource.value = "counter";
      if(cashTransferTarget)  cashTransferTarget.value = "online";
      if(cashTransferAmount)  cashTransferAmount.value = "";
      if(cashTransferNote)    cashTransferNote.value   = "";
      syncCashTransfer();
      openWalletProfitModal(cashTransferModal);
    }
  });

  // Close buttons
  document.querySelectorAll("[data-cash-transfer-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{ cashTransferModal?.classList.remove("show"); });
  });
  cashTransferModal?.addEventListener("click", evt=>{
    if(evt.target === cashTransferModal) cashTransferModal.classList.remove("show");
  });

  // Live sync
  cashTransferSource?.addEventListener("change", syncCashTransfer);
  cashTransferTarget?.addEventListener("change", syncCashTransfer);
  cashTransferAmount?.addEventListener("input",  syncCashTransfer);

  syncCashTransfer();

  openWalletRefreshTrigger?.addEventListener("click", ()=>{
    resetWalletRefreshForm();
    openWalletProfitModal(walletRefreshModal);
  });
  openEasyloadRefreshTrigger?.addEventListener("click", ()=>{
    resetEasyloadRefreshForm();
    openWalletProfitModal(easyloadRefreshModal);
  });
  walletRefreshEasypaisa?.addEventListener("input", syncWalletRefreshPreview);
  walletRefreshJazzcash?.addEventListener("input", syncWalletRefreshPreview);
  easyloadRefreshInputs.forEach(input=>{
    input.addEventListener("input", syncEasyloadRefreshPreview);
  });
  walletRefreshCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  easyloadRefreshCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  walletRefreshModal?.addEventListener("click", evt=>{
    if(evt.target === walletRefreshModal){
      walletRefreshModal.classList.remove("show");
    }
  });
  easyloadRefreshModal?.addEventListener("click", evt=>{
    if(evt.target === easyloadRefreshModal){
      easyloadRefreshModal.classList.remove("show");
    }
  });
  systemCashEntryType?.addEventListener("change", syncSystemCashTypeIcon);
  systemCashReason?.addEventListener("change", syncSystemCashReasonMessage);
  systemCashMessage?.addEventListener("input", ()=>{
    if(systemCashReason?.value !== "custom"){
      delete systemCashMessage.dataset.autoReason;
    }
  });
  openFinanceCashInModal?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    if(financeCategory){
      Array.from(financeCategory.options).forEach(opt => {
        opt.hidden = opt.value === "easyload";
      });
      financeCategory.value = "easypaisa";
    }
    if(financeModeInput){
      financeModeInput.value = "cash_in";
    }
    if(financeNetwork){
      financeNetwork.value = "zong";
    }
    if(financeAmountInput){
      financeAmountInput.value = "";
    }
    if(financeNoteInput){
      financeNoteInput.value = "";
    }
    syncFinanceModal();
    openWalletProfitModal(financeModal);
  });
  openFinanceOutModal?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    if(financeCategory){
      Array.from(financeCategory.options).forEach(opt => {
        opt.hidden = opt.value !== "easyload";
      });
      financeCategory.value = "easyload";
    }
    if(financeModeInput){
      financeModeInput.value = "cash_in";
    }
    if(financeNetwork){
      financeNetwork.value = "zong";
    }
    if(financeAmountInput){
      financeAmountInput.value = "";
    }
    if(financeNoteInput){
      financeNoteInput.value = "";
    }
    syncFinanceModal();
    openWalletProfitModal(financeModal);
  });
  financeModeInput?.addEventListener("change", syncFinanceModal);
  financeCategory?.addEventListener("change", syncFinanceModal);
  financeNetwork?.addEventListener("change", syncFinanceModal);
  financeEasyloadSource?.addEventListener("change", syncFinanceModal);
  financeAmountInput?.addEventListener("input", syncFinanceModal);

  openWalletProfitTrigger?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    if(walletProfitChannel){
      walletProfitChannel.value = "easypaisa";
    }
    if(walletProfitDestination){
      walletProfitDestination.value = "wallet";
    }
    if(walletEntryType){
      walletEntryType.value = "profit_in";
    }
    syncWalletChannelIcon();
    openWalletProfitModal(walletProfitModal);
  });
  openPackageProfitTrigger?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    if(packageProfitEntryType){
      packageProfitEntryType.value = "profit_in";
    }
    if(packageProfitAmountInput){
      packageProfitAmountInput.value = "";
    }
    if(packageProfitNoteInput){
      packageProfitNoteInput.value = "";
    }
    syncPackageProfitForm();
    openWalletProfitModal(packageProfitModal);
  });
  walletProfitChannel?.addEventListener("change", syncWalletChannelIcon);
  walletProfitDestination?.addEventListener("change", syncWalletChannelIcon);
  walletEntryType?.addEventListener("change", syncWalletChannelIcon);
  openEasyloadTrigger?.addEventListener("click", ()=>{
    setQuickActionsOpen(false);
    if(easyloadChannel){
      easyloadChannel.value = "zong";
    }
    if(easyloadEntryType){
      easyloadEntryType.value = "purchase_in";
    }
    if(easyloadAmountInput){
      easyloadAmountInput.value = "";
    }
    if(easyloadNoteInput){
      easyloadNoteInput.value = "";
    }
    syncEasyloadPreview();
    openWalletProfitModal(easyloadModal);
  });
  easyloadChannel?.addEventListener("change", syncEasyloadPreview);
  easyloadEntryType?.addEventListener("change", syncEasyloadPreview);
  easyloadAmountInput?.addEventListener("input", syncEasyloadPreview);
  packageProfitEntryType?.addEventListener("change", syncPackageProfitForm);
  packageProfitReason?.addEventListener("change", syncPackageProfitReasonMessage);
  packageProfitNoteInput?.addEventListener("input", ()=>{
    if(packageProfitReason?.value !== "custom"){
      delete packageProfitNoteInput.dataset.autoReason;
    }
  });
  document.addEventListener("click", evt=>{
    if(!quickActionGroup || !toggleQuickActions){
      return;
    }
    const stack = evt.target.closest(".wallet-fab-stack");
    if(!stack){
      setQuickActionsOpen(false);
    }
  });

  financeCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  walletProfitCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  easyloadCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  packageProfitCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });
  document.querySelectorAll("[data-wallet-history-open]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      let entries = [];
      try{
        entries = JSON.parse(btn.dataset.walletHistoryEntries || "[]");
      }catch(err){
        entries = [];
      }
      openWalletHistoryDetailModal({
        channel: btn.dataset.walletHistoryChannel || "Wallet",
        day: btn.dataset.walletHistoryDay || "",
        total: btn.dataset.walletHistoryTotal || "0.00",
        entries,
      });
    });
  });
  document.querySelectorAll("[data-daily-report-open]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      let entries = [];
      if(btn.dataset.dailyReportEntries){
        try{
          entries = JSON.parse(btn.dataset.dailyReportEntries || "[]");
        }catch(err){
          entries = [];
        }
      }else if(btn.dataset.dailyReportEntry){
        try{
          const parsed = JSON.parse(btn.dataset.dailyReportEntry || "{}");
          entries = parsed && typeof parsed === "object" ? [parsed] : [];
        }catch(err){
          entries = [];
        }
      }
      const title = btn.dataset.dailyReportTitle || "Daily Report";
      openWalletHistoryDetailModal({
        channel: title,
        title: `${title} Details`,
        day: btn.dataset.dailyReportDay || "",
        total: btn.dataset.dailyReportTotal || "0.00",
        totalLabel: btn.dataset.dailyReportTotalLabel || "",
        entries,
      });
    });
  });
  document.querySelectorAll("[data-expense-history-open]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      let entries = [];
      try{
        entries = JSON.parse(btn.dataset.expenseHistoryEntries || "[]");
      }catch(err){
        entries = [];
      }
      openExpenseHistoryDetailModal({
        day: btn.dataset.expenseHistoryDay || "",
        total: btn.dataset.expenseHistoryTotal || "0.00",
        entries,
      });
    });
  });
  document.querySelectorAll("[data-cash-record-info]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      let entry = {};
      try{
        entry = JSON.parse(btn.dataset.cashRecordInfo || "{}");
      }catch(err){
        entry = {};
      }
      openCashRecordInfoModal(entry);
    });
  });
  expenseHistoryFilters.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      currentCashHistoryFilter = btn.dataset.cashHistoryFilter || "all";
      expenseHistoryFilters.forEach(filterBtn=>{
        filterBtn.classList.toggle("active", filterBtn === btn);
      });
      renderExpenseHistoryDetailEntries();
    });
  });
  cashSummaryFilterButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      currentCashSummaryFilter = btn.dataset.cashSummaryFilter || "all";
      cashSummaryFilterButtons.forEach(filterBtn=>{
        filterBtn.classList.toggle("active", filterBtn === btn);
      });
      syncCashSummaryHistory();
    });
  });
  cashDetailFilterButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      currentCashDetailFilter = btn.dataset.cashDetailFilter || "all";
      cashDetailFilterButtons.forEach(filterBtn=>{
        filterBtn.classList.toggle("active", filterBtn === btn);
      });
      syncCashDetailHistory();
    });
  });
  paginatedHistorySections.forEach(section=>{
    document.querySelector(`[data-history-prev="${section}"]`)?.addEventListener("click", ()=>{
      if((historyPaginationState[section] || 1) > 1){
        historyPaginationState[section] -= 1;
        syncPaginatedHistoryTable(section);
      }
    });
    document.querySelector(`[data-history-next="${section}"]`)?.addEventListener("click", ()=>{
      historyPaginationState[section] = (historyPaginationState[section] || 1) + 1;
      syncPaginatedHistoryTable(section);
    });
  });
  walletHistoryTabButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      activateWalletHistoryTab(btn.dataset.walletHistoryTabTarget || "easypaisa");
    });
  });
  document.querySelectorAll("[data-wallet-history-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      walletHistoryDetailModal?.classList.remove("show");
    });
  });
  document.querySelectorAll("[data-expense-history-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      currentCashHistoryFilter = "all";
      expenseHistoryDetailModal?.classList.remove("show");
    });
  });
  document.querySelectorAll("[data-cash-sale-info-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      cashSaleInfoModal?.classList.remove("show");
    });
  });
  document.querySelectorAll("[data-cash-record-info-close]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      cashRecordInfoModal?.classList.remove("show");
    });
  });
  walletHistoryDetailModal?.addEventListener("click", evt=>{
    if(evt.target === walletHistoryDetailModal){
      walletHistoryDetailModal.classList.remove("show");
    }
  });
  expenseHistoryDetailModal?.addEventListener("click", evt=>{
    if(evt.target === expenseHistoryDetailModal){
      currentCashHistoryFilter = "all";
      expenseHistoryDetailModal.classList.remove("show");
    }
  });
  cashSaleInfoModal?.addEventListener("click", evt=>{
    if(evt.target === cashSaleInfoModal){
      cashSaleInfoModal.classList.remove("show");
    }
  });
  cashRecordInfoModal?.addEventListener("click", evt=>{
    if(evt.target === cashRecordInfoModal){
      cashRecordInfoModal.classList.remove("show");
    }
  });
  systemCashCloseButtons.forEach(btn=>{
    btn.addEventListener("click", ()=>{
      closeWalletProfitModal(btn.closest(".modal-backdrop"));
    });
  });

  const profitModalOpen = {{ profit_modal_open|default("")|tojson }};
  const financeModalOpen = {{ finance_modal_open|default("")|tojson }};
  const financeCategoryOpen = {{ finance_category_open|default("")|tojson }};
  const financeNetworkOpen = {{ finance_network_open|default("")|tojson }};
  const managerActivePage = {{ active_page|default("")|tojson }};
  const managerCatalogTab = {{ manage_tab|default("")|tojson }};
  if(profitModalOpen === "system"){
    syncSystemCashTypeIcon();
    openWalletProfitModal(systemCashModal);
  }else if(profitModalOpen === "package"){
    syncPackageProfitForm();
    openWalletProfitModal(packageProfitModal);
  }else if(profitChannelMeta[profitModalOpen]){
    if(walletProfitChannel){
      walletProfitChannel.value = profitModalOpen;
    }
    syncWalletChannelIcon();
    openWalletProfitModal(walletProfitModal);
  }else if(easyloadRates[profitModalOpen]){
    if(easyloadChannel){
      easyloadChannel.value = profitModalOpen;
    }
    syncEasyloadPreview();
    openWalletProfitModal(easyloadModal);
  }
  if(financeModalOpen === "cash_in" || financeModalOpen === "out"){
    if(financeModeInput){
      financeModeInput.value = financeModalOpen;
    }
    if(financeCategory){
      financeCategory.value = financeCategoryOpen || "easypaisa";
    }
      if(financeNetwork && financeNetworkOpen){
        financeNetwork.value = financeNetworkOpen;
      }
    syncFinanceModal();
    openWalletProfitModal(financeModal);
  }
  if(managerActivePage === "sales" && saleChecklist){
    openSalePickerModal();
  }
  {% if active_page == 'easyload_history' %}
  activateWalletHistoryTab("zong");
  {% else %}
  activateWalletHistoryTab("{{ wallet_channels[0].key if wallet_channels else 'easypaisa' }}");
  {% endif %}
  syncSystemCashTypeIcon();
  syncFinanceModal();
  syncWalletChannelIcon();
  syncPackageProfitForm();
  syncEasyloadPreview();
  syncCashSummaryHistory();
  syncCashDetailHistory();
  syncWalletRefreshPreview();
  syncEasyloadRefreshPreview();
  paginatedHistorySections.forEach(syncPaginatedHistoryTable);

  // Dynamic Product Restocks Modal Handling
  const productRestocksModal = document.getElementById("productRestocksModal");
  const restocksTableBody = document.getElementById("restocksTableBody");
  const restocksEmptyState = document.getElementById("restocksEmptyState");
  const restocksTable = document.getElementById("restocksTable");
  const restocksProductTitle = document.getElementById("restocksProductTitle");
  const restocksProductMeta = document.getElementById("restocksProductMeta");

  const closeRestocksModal = () => {
    if (productRestocksModal) {
      productRestocksModal.classList.remove("show");
    }
  };

  document.querySelectorAll("[data-restocks-close]").forEach(btn => {
    btn.addEventListener("click", closeRestocksModal);
  });

  if (productRestocksModal) {
    productRestocksModal.addEventListener("click", (evt) => {
      if (evt.target === productRestocksModal) {
        closeRestocksModal();
      }
    });
  }

  document.addEventListener("click", (evt) => {
    const btn = evt.target.closest(".view-restocks-btn");
    if (!btn) return;
    evt.preventDefault();

    const productId = btn.dataset.productId;
    const productName = btn.dataset.productName;
    const productBrand = btn.dataset.productBrand || "No Brand";
    const productCategory = btn.dataset.productCategory || "Uncategorized";
    const productQty = btn.dataset.productQty || "0";

    if (restocksProductTitle) restocksProductTitle.textContent = productName;
    if (restocksProductMeta) {
      restocksProductMeta.innerHTML = `${productBrand} &middot; ${productCategory} &middot; On Hand: <strong style="color: #fff;">${productQty} units</strong>`;
    }

    if (restocksTableBody) {
      restocksTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--muted);">Loading restock history...</td></tr>`;
    }
    if (restocksTable) restocksTable.hidden = false;
    if (restocksEmptyState) restocksEmptyState.hidden = true;

    if (productRestocksModal) {
      productRestocksModal.classList.add("show");
    }

    fetch(`/manager/products/${productId}/purchases`, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success" && data.entries && data.entries.length > 0) {
        let html = "";
        data.entries.forEach((entry, idx) => {
          const dateStr = entry.batch_date ? new Date(entry.batch_date).toLocaleDateString("en-US", {
            year: "numeric", month: "short", day: "numeric"
          }) : "-";
          const totalSpend = (Number(entry.quantity) * Number(entry.purchase_rate)).toFixed(2);
          html += `
            <tr>
              <td class="product-sr-cell">${idx + 1}</td>
              <td>${dateStr}</td>
              <td><strong style="color: #fff;">${entry.quantity}</strong> units</td>
              <td>PKR ${Number(entry.purchase_rate).toFixed(2)}</td>
              <td><strong style="color: var(--accent-2);">PKR ${totalSpend}</strong></td>
              <td>PKR ${Number(entry.sale_price).toFixed(2)}</td>
            </tr>
          `;
        });
        if (restocksTableBody) restocksTableBody.innerHTML = html;
        if (restocksTable) restocksTable.hidden = false;
        if (restocksEmptyState) restocksEmptyState.hidden = true;
      } else {
        if (restocksTable) restocksTable.hidden = true;
        if (restocksEmptyState) restocksEmptyState.hidden = false;
      }
    })
    .catch(err => {
      console.error("Failed to fetch purchases:", err);
      if (restocksTableBody) {
        restocksTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--danger);">Failed to load history.</td></tr>`;
      }
    });
  });


  // Customer Ledger Functions
  window.openPayDebtModal = function(id, name, balance) {
    document.getElementById('payDebtCustomerName').innerText = name;
    document.getElementById('payDebtBalanceDue').innerText = "PKR " + balance.toFixed(2);
    document.getElementById('payDebtAmount').max = balance;
    document.getElementById('payDebtAmount').value = balance;
    document.getElementById('payDebtForm').action = "/manager/customer/" + id + "/pay";
    document.getElementById('payDebtModal').classList.add('show');
  };

  window.openCustomerHistoryModal = function(id, name, balance) {
    document.getElementById('historyCustomerName').innerText = name;
    document.getElementById('customerHistoryModal').classList.add('show');
    const tbody = document.getElementById('historyTableBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Loading history...</td></tr>';
    
    fetch('/manager/api/customer/' + id + '/history')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          if (data.history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--muted);">No history available.</td></tr>';
            return;
          }
          let html = '';
          data.history.forEach(row => {
            const date = new Date(row.created_at + 'Z').toLocaleString('en-US', {
              day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
            });
            
            let type = row.sale_id ? 'Sale (#' + row.sale_id + ')' : 'Debt Payment';
            
            let itemsHtml = '-';
            if (row.sale_items && row.sale_items.length > 0) {
              const totalItems = row.sale_items.reduce((acc, curr) => acc + curr.quantity, 0);
              const itemsList = row.sale_items.map(i => i.quantity + 'x ' + i.name).join('&#10;');
              itemsHtml = `<span title="${itemsList}" style="cursor: help; text-decoration: underline dotted;">${totalItems} items ℹ️</span>`;
            }
            
            let saleTotal = row.sale_total_amount ? 'PKR ' + row.sale_total_amount.toFixed(2) : '-';
            let amtPaid = row.amount_paid > 0 ? 'PKR ' + row.amount_paid.toFixed(2) : '-';
            let amtDue = row.amount_due > 0 ? '<strong style="color: var(--danger);">PKR ' + row.amount_due.toFixed(2) + '</strong>' : 'PKR 0.00';
            
            html += `<tr>
              <td>${date}</td>
              <td>${type}</td>
              <td>${itemsHtml}</td>
              <td>${saleTotal}</td>
              <td>${amtPaid}</td>
              <td>${amtDue}</td>
            </tr>`;
          });
          tbody.innerHTML = html;
        }
      });
  };

  // Toggle pending amount field if a customer is selected
  (function() {
    const saleCustomerLabelEl = document.getElementById('saleCustomerLabel');
    const pendingAmountContainer = document.getElementById('pendingAmountContainer');
    const pendingAmountInput = document.getElementById('pendingAmount');
    
    // Create an observer to watch for customer selection changes
    const observer = new MutationObserver(function() {
      if (saleCustomerLabelEl && saleCustomerLabelEl.innerText !== 'Select customer') {
        pendingAmountContainer.style.display = 'inline-flex';
      } else {
        pendingAmountContainer.style.display = 'none';
        pendingAmountInput.value = '0';
      }
    });
    
    if (saleCustomerLabelEl) {
      observer.observe(saleCustomerLabelEl, { childList: true, characterData: true, subtree: true });
    }
  })();


