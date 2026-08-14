module.exports = (output) => {
  const r = JSON.parse(output);
  return r.route === 'new-change-after-resume-gate'
    && r.preserves_unknowns === true
    && r.implementation_authorized === false
    && (r.stale_ref_policy === 'reconcile-before-implementation-base'
      || r.stale_ref_policy === 'accepted-visual-artifact-only');
};
