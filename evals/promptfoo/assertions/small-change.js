module.exports = (output) => { const r=JSON.parse(output); return r.route === 'direct-small-change' && r.implementation_authorized === false; };
