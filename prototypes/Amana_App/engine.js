/*
 * Amana — goAML Filing Engine (v0.1)
 * ------------------------------------------------------------------
 * Pure logic layer. Runs in the browser (loaded by index.html) AND in
 * Node.js (for tests). No DOM, no network, no dependencies.
 *
 * What it does:
 *   - Holds the report-type + red-flag-indicator taxonomy for UAE goAML.
 *   - Builds a structured, review-ready STR / REAR / DPMSR narrative.
 *   - Builds well-formed goAML-style XML.
 *   - Validates inputs, applies the AED 55,000 threshold logic and deadlines.
 *
 * IMPORTANT (read the README): the XML here is modelled on the goAML
 * structure to be well-formed and complete, but MUST be reconciled with
 * the UAE FIU's current goAML XSD / import template before any live
 * submission. A licensed MLRO reviews and files. Amana is decision-support.
 */

(function (root) {
  "use strict";

  // ---- Reference data -------------------------------------------------
  var CASH_THRESHOLD_AED = 55000;

  var REPORT_TYPES = {
    STR: {
      code: "STR",
      label: "Suspicious Transaction Report",
      blurb: "File without delay whenever there are reasonable grounds to suspect ML/TF. Event-driven.",
      deadline: "Immediately / without delay upon suspicion.",
      thresholdDriven: false,
      needsIndicators: true,
      needsGrounds: true
    },
    REAR: {
      code: "REAR",
      label: "Real Estate Activity Report",
      blurb: "Mandatory for freehold sale/purchase involving cash (or part-cash) of AED 55,000 or more.",
      deadline: "File on goAML after the qualifying transaction (no suspicion required).",
      thresholdDriven: true,
      needsIndicators: false,
      needsGrounds: false
    },
    DPMSR: {
      code: "DPMSR",
      label: "Dealers in Precious Metals & Stones Report",
      blurb: "Mandatory for a cash/wire transaction of AED 55,000 or more with a customer.",
      deadline: "File within 2 weeks of the qualifying transaction.",
      thresholdDriven: true,
      needsIndicators: false,
      needsGrounds: false
    }
  };

  // Red-flag indicator taxonomy (grouped). Codes are Amana-internal and map
  // to goAML indicator codes in a lookup maintained per FIU schema version.
  var INDICATORS = [
    { group: "Structuring & cash", items: [
      { code: "STR-STRUCT", label: "Payments split to stay under reporting thresholds" },
      { code: "STR-CASHINT", label: "Unusually large or unexplained cash component" },
      { code: "STR-RAPID",  label: "Funds moved in and out rapidly (pass-through)" }
    ]},
    { group: "Source of funds / wealth", items: [
      { code: "STR-SOF",    label: "Source of funds unclear or inconsistent with profile" },
      { code: "STR-SOW",    label: "Source of wealth cannot be reasonably evidenced" },
      { code: "STR-OVERPAY",label: "Overpayment followed by request for refund" }
    ]},
    { group: "Third parties & control", items: [
      { code: "STR-3RDPARTY", label: "Payment from/to an unrelated third party" },
      { code: "STR-NOMINEE",  label: "Apparent use of a nominee / hidden beneficial owner" },
      { code: "STR-UBO",      label: "Reluctance to disclose ultimate beneficial owner" }
    ]},
    { group: "Screening & exposure", items: [
      { code: "STR-PEP",     label: "Customer or UBO is a politically exposed person (PEP)" },
      { code: "STR-SANCTION",label: "Name match against a sanctions / watchlist" },
      { code: "STR-ADVMEDIA",label: "Adverse media linking party to financial crime" }
    ]},
    { group: "Behaviour & geography", items: [
      { code: "STR-EVASIVE", label: "Evasive, reluctant, or provides false information" },
      { code: "STR-URGENCY", label: "Unusual urgency inconsistent with the deal" },
      { code: "STR-HIGHRISK", label: "Link to a high-risk / sanctioned jurisdiction" }
    ]}
  ];

  var TRANSMODE = {
    cash: "C", wire: "T", cheque: "Q", card: "D", crypto: "V", other: "O"
  };

  // ---- Helpers --------------------------------------------------------
  function xmlEscape(s) {
    if (s === undefined || s === null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&apos;");
  }
  function nnum(v) {
    var n = parseFloat(String(v).replace(/[, ]/g, ""));
    return isNaN(n) ? 0 : n;
  }
  function fmtAED(v) {
    var n = nnum(v);
    return "AED " + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function nowISO() { return new Date().toISOString(); }
  function ref(prefix) {
    return prefix + "-" + new Date().toISOString().slice(0, 10).replace(/-/g, "") + "-" +
           Math.random().toString(36).slice(2, 7).toUpperCase();
  }
  function indicatorLabel(code) {
    for (var i = 0; i < INDICATORS.length; i++) {
      for (var j = 0; j < INDICATORS[i].items.length; j++) {
        if (INDICATORS[i].items[j].code === code) return INDICATORS[i].items[j].label;
      }
    }
    return code;
  }
  function safe(d, path, dflt) {
    var parts = path.split("."), cur = d;
    for (var i = 0; i < parts.length; i++) {
      if (cur == null) return dflt;
      cur = cur[parts[i]];
    }
    return (cur === undefined || cur === null || cur === "") ? dflt : cur;
  }

  // ---- Threshold assessment ------------------------------------------
  function assessThreshold(data) {
    var rt = REPORT_TYPES[data.reportType] || REPORT_TYPES.STR;
    var amount = nnum(safe(data, "txn.amount", 0));
    var method = safe(data, "txn.method", "");
    var out = { triggered: false, applicable: rt.thresholdDriven, amount: amount, threshold: CASH_THRESHOLD_AED, note: "" };
    if (!rt.thresholdDriven) {
      out.note = "STR is suspicion-driven; no monetary threshold applies.";
      return out;
    }
    var cashLike = (method === "cash" || method === "wire" || method === "cheque" || method === "crypto");
    if (amount >= CASH_THRESHOLD_AED && cashLike) {
      out.triggered = true;
      out.note = "Amount is at/above AED 55,000 by " + method + " — a " + rt.code + " filing is mandatory.";
    } else if (amount >= CASH_THRESHOLD_AED) {
      out.triggered = true;
      out.note = "Amount is at/above AED 55,000 — confirm payment method; a " + rt.code + " filing is likely mandatory.";
    } else {
      out.note = "Amount is below AED 55,000 — a " + rt.code + " may not be mandatory, but file if suspicious (STR).";
    }
    return out;
  }

  // ---- Validation -----------------------------------------------------
  function validate(data) {
    var rt = REPORT_TYPES[data.reportType] || REPORT_TYPES.STR;
    var errors = [], warnings = [];

    if (!safe(data, "entity.name")) errors.push("Reporting entity name is required.");
    if (!safe(data, "entity.mlroName")) errors.push("MLRO name is required (the accountable person).");
    if (!safe(data, "subject.fullName")) errors.push("Subject name is required.");
    if (!safe(data, "txn.date")) warnings.push("Transaction date is missing.");
    if (!nnum(safe(data, "txn.amount", 0))) warnings.push("Transaction amount is missing or zero.");

    if (safe(data, "subject.kind") === "entity" && !safe(data, "subject.uboName")) {
      warnings.push("Subject is an entity but no ultimate beneficial owner (UBO) is recorded.");
    }
    if (rt.needsIndicators && (!data.indicators || data.indicators.length === 0)) {
      errors.push("At least one red-flag indicator is required for an STR.");
    }
    if (rt.needsGrounds && !safe(data, "grounds")) {
      errors.push("Grounds for suspicion (narrative) are required for an STR.");
    }

    var th = assessThreshold(data);
    if (rt.thresholdDriven && !th.triggered) {
      warnings.push("Amount is below the AED 55,000 threshold for a " + rt.code + ".");
    }
    var screeningHit = safe(data, "screening.sanctions") === "yes" || safe(data, "screening.pep") === "yes";
    if (screeningHit && data.reportType !== "STR") {
      warnings.push("A PEP/sanctions hit was recorded — consider also filing an STR and freezing per TFS rules.");
    }

    return {
      ok: errors.length === 0,
      errors: errors,
      warnings: warnings,
      threshold: th,
      deadline: rt.deadline
    };
  }

  // ---- Narrative generator -------------------------------------------
  function buildNarrative(data) {
    var rt = REPORT_TYPES[data.reportType] || REPORT_TYPES.STR;
    var L = [];
    var entityName = safe(data, "entity.name", "[Reporting entity]");
    var entityType = safe(data, "entity.type", "DNFBP");
    var license = safe(data, "entity.licenseNo", "[license no.]");
    var mlro = safe(data, "entity.mlroName", "[MLRO]");
    var preparedBy = safe(data, "preparedBy", mlro);
    var subjKind = safe(data, "subject.kind", "person");
    var subjName = safe(data, "subject.fullName", "[subject]");

    L.push(rt.label.toUpperCase() + " — NARRATIVE");
    L.push("Reference: " + ref(rt.code) + "   |   Prepared: " + nowISO().slice(0, 16).replace("T", " ") + " (UTC)");
    L.push("Prepared by " + preparedBy + ", MLRO for " + entityName + " (license " + license + ").");
    L.push("");

    L.push("1. REPORTING CONTEXT");
    L.push(entityName + " is a " + entityType + " subject to UAE AML/CFT obligations and registered on goAML. " +
      "This " + rt.code + " concerns " + (subjKind === "entity" ? "an entity, " : "an individual, ") + subjName + ".");
    L.push("");

    L.push("2. SUBJECT OF THE REPORT");
    if (subjKind === "entity") {
      L.push("Entity name: " + subjName +
        " | Trade licence: " + safe(data, "subject.tradeLicense", "[not provided]") +
        " | Registered address: " + safe(data, "subject.address", "[not provided]") + ".");
      L.push("Ultimate beneficial owner (UBO): " + safe(data, "subject.uboName", "[not identified]") +
        " (" + safe(data, "subject.uboNationality", "nationality unknown") + ", ID " +
        safe(data, "subject.uboIdNumber", "[not provided]") + ").");
    } else {
      L.push("Full name: " + subjName +
        " | Nationality: " + safe(data, "subject.nationality", "[not provided]") +
        " | " + safe(data, "subject.idType", "ID") + ": " + safe(data, "subject.idNumber", "[not provided]") +
        " | DOB: " + safe(data, "subject.dob", "[not provided]") + ".");
      L.push("Address: " + safe(data, "subject.address", "[not provided]") + ".");
    }
    L.push("");

    L.push("3. TRANSACTION(S)");
    var amount = fmtAED(safe(data, "txn.amount", 0));
    var method = safe(data, "txn.method", "unspecified method");
    var dir = safe(data, "txn.direction", "");
    var cp = safe(data, "txn.counterparty", "[counterparty not provided]");
    var tdate = safe(data, "txn.date", "[date not provided]");
    var line = "On " + tdate + ", a transaction of " + amount + " was conducted by " + method +
      (dir ? " (" + dir + ")" : "") + ", counterparty: " + cp + ".";
    if (data.reportType === "REAR") {
      line += " Property reference: " + safe(data, "txn.propertyRef", "[not provided]") + ".";
    }
    if (data.reportType === "DPMSR") {
      line += " Goods: " + safe(data, "txn.goodsDesc", "[precious metals/stones — not described]") + ".";
    }
    L.push(line);
    var th = assessThreshold(data);
    if (rt.thresholdDriven) L.push("Threshold check: " + th.note);
    L.push("");

    if (rt.needsIndicators) {
      L.push("4. INDICATORS OBSERVED");
      if (data.indicators && data.indicators.length) {
        data.indicators.forEach(function (c, i) { L.push("  (" + (i + 1) + ") " + indicatorLabel(c) + "  [" + c + "]"); });
      } else {
        L.push("  [No indicators selected]");
      }
      L.push("");

      L.push("5. GROUNDS FOR SUSPICION");
      L.push(safe(data, "grounds", "[Grounds for suspicion not provided]"));
      var scr = [];
      if (safe(data, "screening.pep") === "yes") scr.push("PEP match identified");
      if (safe(data, "screening.sanctions") === "yes") scr.push("sanctions/watchlist match identified");
      if (scr.length) L.push("Screening: " + scr.join("; ") + ".");
      L.push("On the basis of the above, customer due diligence is considered unsatisfactory and the activity is reported as suspicious.");
      L.push("");
    } else {
      L.push("4. BASIS FOR FILING");
      L.push("This is a mandatory threshold report (" + rt.blurb + ") No suspicion determination is asserted by the filing itself.");
      L.push("");
    }

    L.push((rt.needsIndicators ? "6" : "5") + ". ACTION TAKEN");
    L.push(safe(data, "action", "[Action not recorded — e.g. transaction held / proceeded / relationship under review]."));
    L.push("Deadline: " + rt.deadline);
    L.push("");
    L.push("— Filed via Amana. A licensed MLRO has reviewed this report prior to submission.");

    return L.join("\n");
  }

  // ---- goAML XML generator -------------------------------------------
  function buildGoAmlXml(data) {
    var rt = REPORT_TYPES[data.reportType] || REPORT_TYPES.STR;
    var e = xmlEscape;
    var amount = nnum(safe(data, "txn.amount", 0));
    var transmode = TRANSMODE[safe(data, "txn.method", "other")] || "O";
    var subjKind = safe(data, "subject.kind", "person");

    var partyBlock;
    if (subjKind === "entity") {
      partyBlock =
        "        <t_entity>\n" +
        "          <name>" + e(safe(data, "subject.fullName")) + "</name>\n" +
        "          <incorporation_number>" + e(safe(data, "subject.tradeLicense")) + "</incorporation_number>\n" +
        "          <address><address>" + e(safe(data, "subject.address")) + "</address><country>AE</country></address>\n" +
        "          <director_id>\n" +
        "            <first_name>" + e(safe(data, "subject.uboName")) + "</first_name>\n" +
        "            <role>Ultimate Beneficial Owner</role>\n" +
        "          </director_id>\n" +
        "        </t_entity>";
    } else {
      partyBlock =
        "        <t_person>\n" +
        "          <first_name>" + e(safe(data, "subject.fullName")) + "</first_name>\n" +
        "          <nationality1>" + e(safe(data, "subject.nationality")) + "</nationality1>\n" +
        "          <ssn>" + e(safe(data, "subject.idNumber")) + "</ssn>\n" +
        "          <birthdate>" + e(safe(data, "subject.dob")) + "</birthdate>\n" +
        "          <address><address>" + e(safe(data, "subject.address")) + "</address><country>AE</country></address>\n" +
        "        </t_person>";
    }

    var indicatorsXml = "";
    if (rt.needsIndicators && data.indicators && data.indicators.length) {
      indicatorsXml = "  <report_indicators>\n" +
        data.indicators.map(function (c) { return "    <indicator>" + e(c) + "</indicator>"; }).join("\n") +
        "\n  </report_indicators>\n";
    }

    var reason = rt.needsGrounds
      ? safe(data, "grounds", "")
      : "Mandatory threshold report (" + rt.label + "). Transaction at/above AED 55,000.";

    var xml =
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<report xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n' +
      "  <rentity_id>" + e(safe(data, "entity.rentityId", "0")) + "</rentity_id>\n" +
      "  <submission_code>E</submission_code>\n" +
      "  <report_code>" + e(rt.code) + "</report_code>\n" +
      "  <entity_reference>" + e(ref(rt.code)) + "</entity_reference>\n" +
      "  <submission_date>" + e(nowISO()) + "</submission_date>\n" +
      "  <currency_code_local>AED</currency_code_local>\n" +
      "  <reporting_person>\n" +
      "    <first_name>" + e(safe(data, "entity.mlroName")) + "</first_name>\n" +
      "    <email>" + e(safe(data, "entity.mlroEmail")) + "</email>\n" +
      "    <occupation>MLRO</occupation>\n" +
      "  </reporting_person>\n" +
      "  <location><address>" + e(safe(data, "entity.emirate", "Dubai")) + "</address><country>AE</country></location>\n" +
      "  <reason>" + e(reason) + "</reason>\n" +
      "  <action>" + e(safe(data, "action", "")) + "</action>\n" +
      "  <transaction>\n" +
      "    <transactionnumber>" + e(ref("TXN")) + "</transactionnumber>\n" +
      "    <transaction_location>" + e(safe(data, "entity.emirate", "Dubai")) + "</transaction_location>\n" +
      "    <date_transaction>" + e(safe(data, "txn.date")) + "</date_transaction>\n" +
      "    <transmode_code>" + e(transmode) + "</transmode_code>\n" +
      "    <amount_local>" + amount.toFixed(2) + "</amount_local>\n" +
      "    <t_to>\n" +
      "      <t_to_my_client>\n" +
      partyBlock + "\n" +
      "      </t_to_my_client>\n" +
      "    </t_to>\n" +
      "  </transaction>\n" +
      indicatorsXml +
      "</report>\n";

    return xml;
  }

  // ---- Public API -----------------------------------------------------
  var Engine = {
    CASH_THRESHOLD_AED: CASH_THRESHOLD_AED,
    REPORT_TYPES: REPORT_TYPES,
    INDICATORS: INDICATORS,
    assessThreshold: assessThreshold,
    validate: validate,
    buildNarrative: buildNarrative,
    buildGoAmlXml: buildGoAmlXml,
    indicatorLabel: indicatorLabel,
    _helpers: { xmlEscape: xmlEscape, fmtAED: fmtAED, nnum: nnum }
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = Engine;   // Node (tests)
  } else {
    root.AmanaEngine = Engine;  // Browser (index.html)
  }
})(typeof window !== "undefined" ? window : this);
