var dagfuncs = (window.dashAgGridFunctions = window.dashAgGridFunctions || {});

dagfuncs.numericDisplayComparator = function (valueA, valueB) {
  function toNumber(value) {
    if (value === null || value === undefined || value === "") {
      return Number.NEGATIVE_INFINITY;
    }
    if (typeof value === "number") {
      return Number.isNaN(value) ? Number.NEGATIVE_INFINITY : value;
    }
    var cleaned = String(value).replace(/[^0-9.\-]/g, "");
    if (!cleaned) {
      return Number.NEGATIVE_INFINITY;
    }
    var parsed = parseFloat(cleaned);
    return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
  }

  return toNumber(valueA) - toNumber(valueB);
};
