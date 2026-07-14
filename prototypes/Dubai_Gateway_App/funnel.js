/*
 * The Dubai Gateway — funnel & tools engine (pressure-test MVP)
 * ------------------------------------------------------------------
 * Pure logic. Runs in the browser (index.html) and Node (tests).
 *   - calcROI: rental yield + appreciation projection (the lead magnet)
 *   - checkGoldenVisa: property-route visa eligibility (the lead magnet)
 *   - qualifyLead: scores a captured lead Hot/Warm/Cold
 *   - funnelModel: the pressure-test — CPL, CPQL, CAC/deal, ROAS,
 *     break-even CPQL vs the AED 100k+ commission per deal.
 *
 * Figures (area yields, visa thresholds) are directional as of mid-2026
 * and must be confirmed against official/live sources. Not advice.
 */
(function (root) {
  "use strict";

  // Indicative gross rental yields by popular Dubai area (directional).
  var AREA_YIELDS = {
    "Jumeirah Village Circle (JVC)": 0.081,
    "Business Bay": 0.066,
    "Dubai Marina": 0.061,
    "Dubai Hills Estate": 0.055,
    "Downtown Dubai": 0.050,
    "Palm Jumeirah": 0.045,
    "Dubai Creek Harbour": 0.058,
    "Jumeirah Lake Towers (JLT)": 0.072
  };

  var GOLDEN_VISA_THRESHOLD = 2000000;   // AED — 10-year Golden Visa (property route)
  var INVESTOR_VISA_THRESHOLD = 750000;  // AED — 2-year property investor visa

  function num(v) { var n = parseFloat(String(v == null ? "" : v).replace(/[^0-9.\-]/g, "")); return isNaN(n) ? 0 : n; }
  function round(n, d) { var f = Math.pow(10, d || 0); return Math.round(n * f) / f; }
  function aed(n) { return "AED " + Math.round(n).toLocaleString("en-US"); }
  function pct(n, d) { return round(n * 100, d == null ? 1 : d) + "%"; }

  // ---- ROI calculator -------------------------------------------------
  function calcROI(o) {
    o = o || {};
    var price = num(o.price);
    var gy = o.grossYield != null ? num(o.grossYield) : (AREA_YIELDS[o.area] || 0.06);
    if (gy > 1) gy = gy / 100; // accept 6 or 0.06
    var mgmt = o.costRatio != null ? num(o.costRatio) : 0.25; // service charge + mgmt + vacancy
    if (mgmt > 1) mgmt = mgmt / 100;
    var appr = o.appreciation != null ? num(o.appreciation) : 0.07;
    if (appr > 1) appr = appr / 100;
    var years = num(o.years) || 5;
    var downPct = o.downPaymentPct != null ? num(o.downPaymentPct) : 1;
    if (downPct > 1) downPct = downPct / 100;

    var annualRent = price * gy;
    var netAnnual = annualRent * (1 - mgmt);
    var netYield = price ? netAnnual / price : 0;
    var futureValue = price * Math.pow(1 + appr, years);
    var appreciationGain = futureValue - price;
    var rentOverYears = netAnnual * years;
    var totalProfit = rentOverYears + appreciationGain;
    var invested = price * downPct;
    var totalReturnPctOnInvested = invested ? totalProfit / invested : 0;

    return {
      price: price, grossYield: gy, netYield: netYield,
      annualRent: annualRent, netAnnual: netAnnual, monthlyNet: netAnnual / 12,
      years: years, futureValue: futureValue, appreciationGain: appreciationGain,
      rentOverYears: rentOverYears, totalProfit: totalProfit,
      invested: invested, totalReturnPctOnInvested: totalReturnPctOnInvested,
      goldenVisa: checkGoldenVisa(price)
    };
  }

  // ---- Golden Visa eligibility ---------------------------------------
  function checkGoldenVisa(amount) {
    var a = num(amount);
    if (a >= GOLDEN_VISA_THRESHOLD) {
      return { eligible: true, tier: "10-Year Golden Visa", threshold: GOLDEN_VISA_THRESHOLD,
        note: "A property worth AED 2M+ (owned or mortgaged) qualifies for the 10-year Golden Visa.",
        shortfall: 0 };
    }
    if (a >= INVESTOR_VISA_THRESHOLD) {
      return { eligible: true, tier: "2-Year Property Investor Visa", threshold: INVESTOR_VISA_THRESHOLD,
        note: "Qualifies for a 2-year investor visa. Reach AED 2M to unlock the 10-year Golden Visa.",
        shortfall: GOLDEN_VISA_THRESHOLD - a };
    }
    return { eligible: false, tier: "Not eligible via property alone", threshold: INVESTOR_VISA_THRESHOLD,
      note: "Below the AED 750k property route. Consider a larger allocation or another visa category.",
      shortfall: INVESTOR_VISA_THRESHOLD - a };
  }

  // ---- Lead qualification --------------------------------------------
  // input: { budget (AED), purpose, timeline, financing }
  function qualifyLead(o) {
    o = o || {};
    var budget = num(o.budget);
    var s = 0, reasons = [];

    if (budget >= 2000000) { s += 3; reasons.push("Budget AED 2M+ (Golden Visa + top commission)"); }
    else if (budget >= 1000000) { s += 2; reasons.push("Budget AED 1–2M"); }
    else if (budget >= 500000) { s += 1; reasons.push("Budget AED 500k–1M"); }
    else reasons.push("Budget below AED 500k");

    var purpose = (o.purpose || "").toLowerCase();
    if (purpose.indexOf("visa") >= 0 || purpose.indexOf("residenc") >= 0) { s += 3; reasons.push("Residency/Golden-Visa intent"); }
    else if (purpose.indexOf("invest") >= 0) { s += 2; reasons.push("Investment intent"); }
    else if (purpose.indexOf("reloc") >= 0 || purpose.indexOf("live") >= 0) { s += 2; reasons.push("Relocation intent"); }
    else reasons.push("Browsing / undecided");

    var t = (o.timeline || "").toLowerCase();
    if (t.indexOf("0-3") >= 0 || t.indexOf("<3") >= 0 || t.indexOf("ready") >= 0) { s += 3; reasons.push("Buying in 0–3 months"); }
    else if (t.indexOf("3-6") >= 0) { s += 2; reasons.push("Buying in 3–6 months"); }
    else if (t.indexOf("6-12") >= 0) { s += 1; reasons.push("Buying in 6–12 months"); }
    else reasons.push("No firm timeline");

    var f = (o.financing || "").toLowerCase();
    if (f.indexOf("cash") >= 0) { s += 2; reasons.push("Cash buyer"); }
    else if (f.indexOf("pre") >= 0 || f.indexOf("approved") >= 0) { s += 2; reasons.push("Mortgage pre-approved"); }
    else if (f.indexOf("mortgage") >= 0 || f.indexOf("finance") >= 0) { s += 1; reasons.push("Needs mortgage"); }

    var tier = s >= 7 ? "Hot" : s >= 4 ? "Warm" : "Cold";
    var qualified = (s >= 5 && budget >= 1000000);
    return { score: s, maxScore: 11, tier: tier, qualified: qualified, reasons: reasons };
  }

  // ---- Funnel economics (the pressure-test) --------------------------
  // input: { spend, cpl, leadToQualified, qualifiedToClose, ticket, commissionPct, otherMonthlyCost }
  function funnelModel(o) {
    o = o || {};
    var spend = num(o.spend);
    var cpl = num(o.cpl) || 1;
    var l2q = o.leadToQualified != null ? num(o.leadToQualified) : 0.25; if (l2q > 1) l2q /= 100;
    var q2c = o.qualifiedToClose != null ? num(o.qualifiedToClose) : 0.06; if (q2c > 1) q2c /= 100;
    var ticket = num(o.ticket) || 2700000;
    var commissionPct = o.commissionPct != null ? num(o.commissionPct) : 0.05; if (commissionPct > 1) commissionPct /= 100;
    var other = num(o.otherMonthlyCost);

    var commissionPerDeal = ticket * commissionPct;
    var leads = spend / cpl;
    var qualified = leads * l2q;
    var deals = qualified * q2c;
    var cpql = qualified ? spend / qualified : 0;
    var cacPerDeal = deals ? (spend + other) / deals : 0;
    var revenue = deals * commissionPerDeal;
    var totalCost = spend + other;
    var grossProfit = revenue - totalCost;
    var roas = totalCost ? revenue / totalCost : 0;
    var margin = revenue ? grossProfit / revenue : 0;

    // Break-even: the most you can pay per qualified lead and still profit
    var breakEvenCpql = commissionPerDeal * q2c;           // spend per qualified lead == expected commission per qualified lead
    var breakEvenCloseRate = commissionPerDeal ? cpql / commissionPerDeal : 0; // close rate needed to break even at current CPQL
    var headroom = cpql ? breakEvenCpql / cpql : 0;        // how many x you could overpay per qualified lead

    return {
      commissionPerDeal: commissionPerDeal,
      leads: leads, qualified: qualified, deals: deals,
      cpl: cpl, cpql: cpql, cacPerDeal: cacPerDeal,
      revenue: revenue, totalCost: totalCost, grossProfit: grossProfit, roas: roas, margin: margin,
      breakEvenCpql: breakEvenCpql, breakEvenCloseRate: breakEvenCloseRate, headroom: headroom,
      profitable: grossProfit > 0,
      verdict: grossProfit > 0
        ? "PROFITABLE — at these numbers you can pay up to " + aed(breakEvenCpql) + " per qualified lead and still break even. You're at " + aed(cpql) + " (" + round(headroom, 1) + "x headroom)."
        : "NOT YET — CAC/deal (" + aed(cacPerDeal) + ") exceeds the " + aed(commissionPerDeal) + " commission. Raise close rate above " + pct(breakEvenCloseRate) + " or lower CPQL below " + aed(breakEvenCpql) + "."
    };
  }

  var API = {
    AREA_YIELDS: AREA_YIELDS, GOLDEN_VISA_THRESHOLD: GOLDEN_VISA_THRESHOLD, INVESTOR_VISA_THRESHOLD: INVESTOR_VISA_THRESHOLD,
    calcROI: calcROI, checkGoldenVisa: checkGoldenVisa, qualifyLead: qualifyLead, funnelModel: funnelModel,
    fmt: { aed: aed, pct: pct, num: num, round: round }
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.Gateway = API;
})(typeof window !== "undefined" ? window : this);
