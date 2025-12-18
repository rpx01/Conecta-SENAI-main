(function(){
  const $doc = document;

  $doc.addEventListener('keydown', (e) => {
    if(e.key === 'Escape'){
      const opened = $doc.querySelector('.filter-btn[aria-expanded="true"]');
      if(opened){ opened.click(); }
    }
  });

  $doc.addEventListener('input', (e) => {
    const input = e.target.closest('input[data-role="filter-search"]');
    if(!input) return;
    const wrap = input.closest('.filter-menu');
    const q = input.value.trim().toLowerCase();
    
    wrap.querySelectorAll('[data-role="filter-options"] .form-check').forEach(box=>{
      const label = box.textContent.trim().toLowerCase();
      box.style.display = label.includes(q) ? '' : 'none';
    });
  });

  $doc.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if(!btn) return;

    const menu = btn.closest('.filter-menu');
    const thBtn = menu?.parentElement?.querySelector('.filter-btn');
    const col = thBtn?.getAttribute('data-col');

    const selected = Array.from(menu.querySelectorAll('[data-role="filter-options"] input[type="checkbox"]:checked'))
      .map(i => i.value);

    switch(btn.getAttribute('data-action')){
      case 'apply':
        
        window.aplicarFiltro && window.aplicarFiltro(col, selected);
        break;
      case 'clear':
        menu.querySelectorAll('[data-role="filter-options"] input[type="checkbox"]').forEach(i=> i.checked = true);
        window.limparFiltro && window.limparFiltro(col);
        break;
      case 'sort-asc':
        window.ordenarColuna && window.ordenarColuna(col, 'asc');
        break;
      case 'sort-desc':
        window.ordenarColuna && window.ordenarColuna(col, 'desc');
        break;
    }
  }, false);
})();
