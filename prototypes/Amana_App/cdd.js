/*
 * Amana — CDD & UBO module (v0.1)
 * ------------------------------------------------------------------
 * Pure logic. Runs in the browser (index.html) and Node (tests).
 *
 *  - traceUBO(subject): walks an ownership tree, multiplies percentages
 *    down each chain, aggregates per natural person, and identifies the
 *    Ultimate Beneficial Owner(s) at the >=25% UAE control threshold.
 *    Falls back to "senior managing official" when no one qualifies.
 *  - riskRate(factors): transparent CDD risk score -> Low/Medium/High
 *    plus the concrete actions the MLRO must take.
 *
 * No legal advice; a licensed MLRO owns the final determination.
 */
(function (root) {
  "use strict";

  function num(v) { var n = parseFloat(String(v).replace(/[%, ]/g, "")); return isNaN(n) ? 0 : n; }
  function round(n, d) { var f = Math.pow(10, d || 2); return Math.round(n * f) / f; }

  /*
   * subject = {
   *   name, kind:"entity",
   *   owners:[ { name, kind:"person"|"entity", percent, nationality?, idNumber?, owners?:[...] } ]
   * }
   */
  function traceUBO(subject, opts) {
    opts = opts || {};
    var threshold = opts.threshold != null ? opts.threshold : 25;
    var maxDepth = opts.maxDepth || 12;
    var persons = {};   // key -> aggregated person
    var maxHops = 0;    // longest chain (in ownership hops) from subject down to a natural person

    function walk(node, cumFrac, pathLabels, depth) {
      if (depth > maxDepth) return;
      var owners = node.owners || [];
      owners.forEach(function (o) {
        var pct = num(o.percent);
        var frac = cumFrac * (pct / 100);
        var step = round(pct, 2) + "% of " + (node.name || "the subject");
        var path = pathLabels.concat([step]);
        if (o.kind === "entity") {
          walk(o, frac, path, depth + 1);
        } else {
          var hops = depth + 1;
          if (hops > maxHops) maxHops = hops;
          var key = (o.name || "[unnamed]").toLowerCase().trim();
          if (!persons[key]) {
            persons[key] = { name: o.name || "[unnamed]", nationality: o.nationality || "",
                             idNumber: o.idNumber || "", effective: 0, chains: [] };
          }
          persons[key].effective += frac * 100;
          persons[key].chains.push({ percent: round(frac * 100, 2), path: path.join("  →  ") });
        }
      });
    }

    walk(subject, 1, [], 0);

    var list = Object.keys(persons).map(function (k) {
      persons[k].effective = round(persons[k].effective, 2);
      return persons[k];
    }).sort(function (a, b) { return b.effective - a.effective; });

    var ubos = list.filter(function (p) { return p.effective >= threshold - 1e-9; });
    var result = {
      threshold: threshold,
      persons: list,
      ubos: ubos,
      hasUBO: ubos.length > 0,
      layers: maxHops,
      totalTraced: round(list.reduce(function (s, p) { return s + p.effective; }, 0), 2)
    };
    if (!result.hasUBO) {
      result.fallback =
        "No natural person meets the " + threshold + "% ownership test. Under UAE rules, next identify " +
        "any person controlling the entity by other means (voting rights, right to appoint/remove directors); " +
        "failing that, record the senior managing official as the UBO.";
    }
    return result;
  }

  // Human-readable one-liner per UBO, e.g.
  //   "Ahmed Ben Salah — 30% (via 60% of Marina Holdings  →  50% of Gulf Trading)"
  function describeUBO(p) {
    var best = p.chains.slice().sort(function (a, b) { return b.percent - a.percent; })[0];
    return p.name + " — " + p.effective + "%" + (best ? " (via " + best.path + ")" : "");
  }

  var RISK_FACTORS = [
    { key: "sanctionsHit",       label: "Sanctions / watchlist match", weight: 99 },
    { key: "pep",                label: "Politically exposed person (PEP)", weight: 2 },
    { key: "adverseMedia",       label: "Adverse media on customer/UBO", weight: 2 },
    { key: "highRiskJurisdiction", label: "High-risk jurisdiction link", weight: 2 },
    { key: "unclearSOF",         label: "Source of funds/wealth unclear", weight: 2 },
    { key: "nomineeSuspected",   label: "Nominee / hidden ownership suspected", weight: 2 },
    { key: "complexOwnership",   label: "Complex / opaque ownership", weight: 1 },
    { key: "cashIntensive",      label: "Cash-intensive activity", weight: 1 },
    { key: "nonResident",        label: "Non-resident customer", weight: 1 }
  ];

  function riskRate(f) {
    f = f || {};
    var score = 0;
    RISK_FACTORS.forEach(function (r) { if (f[r.key] && r.key !== "sanctionsHit") score += r.weight; });
    var level = score >= 6 ? "High" : score >= 3 ? "Medium" : "Low";
    if (f.sanctionsHit) level = "High";

    var actions = [];
    if (f.sanctionsHit) actions.push("STOP: apparent sanctions match — freeze without delay, do NOT proceed, and file an STR.");
    if (level === "High") {
      actions.push("Enhanced Due Diligence (EDD) required.");
      actions.push("Senior management approval before onboarding/continuing.");
      actions.push("Obtain and evidence source of funds and source of wealth.");
      actions.push("Enhanced ongoing monitoring (e.g. quarterly review).");
    } else if (level === "Medium") {
      actions.push("Additional verification of identity and UBO.");
      actions.push("Periodic review (e.g. annually).");
    } else {
      actions.push("Standard CDD and record-keeping.");
      actions.push("Periodic review per policy.");
    }
    if (f.pep) actions.push("PEP controls: establish source of wealth and apply senior sign-off.");
    if (f.unclearSOF && !f.sanctionsHit) actions.push("Do not proceed until source of funds is satisfactorily evidenced.");

    return { score: score, level: level, actions: actions };
  }

  var CDD = {
    traceUBO: traceUBO,
    describeUBO: describeUBO,
    riskRate: riskRate,
    RISK_FACTORS: RISK_FACTORS,
    _num: num
  };

  if (typeof module !== "undefined" && module.exports) module.exports = CDD;
  else root.AmanaCDD = CDD;
})(typeof window !== "undefined" ? window : this);
