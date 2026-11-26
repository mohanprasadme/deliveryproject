(function () {
  var tbody = document.getElementById('itemRows');
  var tpl = document.getElementById('rowTemplate');
  var total = document.querySelector('input[name="items-TOTAL_FORMS"]');


  // Update the challan colour theme immediately when Returnable / Non Returnable changes.
  function updateChallanTheme() {
    var paper = document.getElementById('challanPaper');
    if (!paper) return;
    var selected = document.querySelector('input[name="challan_type"]:checked');
    var isReturnable = selected && selected.value === 'R';
    paper.classList.toggle('type-returnable', !!isReturnable);
    paper.classList.toggle('type-non-returnable', !isReturnable);
  }

  document.querySelectorAll('input[name="challan_type"]').forEach(function (radio) {
    radio.addEventListener('change', updateChallanTheme);
  });
  updateChallanTheme();

  function visibleRows() {
    return Array.prototype.filter.call(tbody.querySelectorAll('tr.item-row'),
      function (tr) { return tr.style.display !== 'none'; });
  }
  function renumber() {
    visibleRows().forEach(function (tr, i) { tr.querySelector('.sno').textContent = i + 1; });
  }
  function addRow() {
    var idx = parseInt(total.value, 10);
    tbody.insertAdjacentHTML('beforeend', tpl.innerHTML.replace(/__prefix__/g, idx));
    total.value = idx + 1;
    renumber();
    var rows = tbody.querySelectorAll('tr.item-row');
    var field = rows[rows.length - 1].querySelector('textarea');
    if (field) field.focus();
  }

  // hide rows that were already marked for deletion (after a validation error)
  tbody.querySelectorAll('tr.item-row').forEach(function (tr) {
    var cb = tr.querySelector('input[type=checkbox][name$="-DELETE"]');
    if (cb && cb.checked) tr.style.display = 'none';
  });

  tbody.addEventListener('click', function (e) {
    var btn = e.target.closest('.remove-row');
    if (!btn) return;
    var tr = btn.closest('tr');
    var cb = tr.querySelector('input[type=checkbox][name$="-DELETE"]');
    if (cb) cb.checked = true;
    tr.style.display = 'none';
    if (visibleRows().length === 0) addRow(); else renumber();
  });

  document.getElementById('addRow').addEventListener('click', addRow);
  renumber();
})();
