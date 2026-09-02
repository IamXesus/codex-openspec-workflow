module.exports = (output) => {
  const r = JSON.parse(output);
  return r.route === 'continue-without-acceptance' &&
    r.preserves_unknowns === true &&
    r.implementation_authorized === false;
};
