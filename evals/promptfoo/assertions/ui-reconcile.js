module.exports = (output) => { const r=JSON.parse(output); return r.route === 'ui-contract-reconciliation' && r.reconcile_ui_before_code === true && r.implementation_authorized === false; };
