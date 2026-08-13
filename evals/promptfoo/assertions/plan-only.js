module.exports = (output) => { const r=JSON.parse(output); return r.route === 'openspec-plan' && r.preserves_unknowns === true && r.implementation_authorized === false; };
