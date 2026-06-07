
  document.addEventListener("click", evt=>{
    const trigger = evt.target.closest("[data-modal-open]");
    if(!trigger){
      return;
    }
    const targetId = trigger.getAttribute("data-modal-open");
    if(!targetId){
      return;
    }
    const modal = document.getElementById(targetId);
    if(!modal){
      return;
    }
    modal.classList.add("show");
    if(targetId === "salePickerModal"){
      document.getElementById("saleProductSearch")?.focus();
    }
  });
