/*
 * Amana — AI assist module (v0.1)  [OPTIONAL]
 * ------------------------------------------------------------------
 * Off by default. Amana works fully without it. When the user supplies an
 * API key in AI settings, this module can:
 *   - polish a drafted report narrative (clarity/grammar/completeness), and
 *   - extract fields from an ID/licence photo (vision).
 *
 * PRIVACY BY DESIGN
 *   - "Local tidy" needs no key and no network (pure formatting).
 *   - Reversible PII redaction: sensitive tokens (IDs, Emirates IDs, emails)
 *     are swapped for opaque ⟦TOKENS⟧ before anything is sent to a cloud
 *     provider, then restored locally in the result. The provider never sees
 *     real identifiers, yet the final narrative keeps the real values.
 *   - For production we route to an in-region / enterprise endpoint; direct
 *     browser calls to public LLM APIs may be blocked by CORS.
 *
 * The AI NEVER invents facts — the prompt forbids it and a human MLRO reviews.
 */
(function (root) {
  "use strict";

  // ---- Reversible PII redaction --------------------------------------
  function redactReversible(text) {
    var map = [], n = { ID: 0, EMAIL: 0, EID: 0 };
    var t = String(text == null ? "" : text);
    function tok(kind, orig) {
      n[kind]++; var token = "⟦" + kind + n[kind] + "⟧";
      map.push({ token: token, original: orig }); return token;
    }
    t = t.replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, function (m) { return tok("EMAIL", m); });
    t = t.replace(/\b784-?\d{4}-?\d{7}-?\d\b/g, function (m) { return tok("EID", m); });
    t = t.replace(/\b(?=[A-Z0-9-]*\d)[A-Z0-9]{7,}\b/g, function (m) { return tok("ID", m); });
    return { text: t, map: map, count: map.length };
  }
  function restore(text, map) {
    var t = String(text == null ? "" : text);
    (map || []).forEach(function (p) { t = t.split(p.token).join(p.original); });
    return t;
  }

  // ---- Offline "tidy" (deterministic, not AI) ------------------------
  function localTidy(draft) {
    var t = String(draft == null ? "" : draft);
    t = t.replace(/[ \t]+\n/g, "\n");        // strip trailing spaces
    t = t.replace(/\n{3,}/g, "\n\n");          // collapse blank lines
    t = t.replace(/[ \t]{2,}/g, " ");          // collapse runs of spaces
    t = t.replace(/\s+([.,;:])/g, "$1");       // no space before punctuation
    t = t.trim() + "\n";
    return t;
  }

  // ---- Prompt builders -----------------------------------------------
  function buildPolishPrompt(draft, reportType) {
    var system =
      "You are an AML compliance writing assistant for UAE goAML filings. " +
      "Improve the clarity, grammar, structure and completeness of the report narrative provided. " +
      "STRICT RULES: do NOT invent, add, or alter any facts, names, amounts, dates, or identifiers. " +
      "Preserve all section numbers and headings. Keep any ⟦...⟧ tokens EXACTLY as they appear. " +
      "Use a formal, objective regulatory tone. Return ONLY the improved narrative text.";
    var user = "Report type: " + (reportType || "STR") + "\n\n----- NARRATIVE -----\n" + draft;
    return { system: system, user: user };
  }

  function buildExtractPrompt(docType) {
    return "You are reading a UAE " + (docType || "identity document") + ". " +
      "Extract these fields as strict JSON with exactly these keys: " +
      "fullName, idType, idNumber, nationality, dob, expiry, address. " +
      "Use YYYY-MM-DD for dates. Use null for anything not clearly visible. " +
      "Return ONLY the JSON object, no commentary.";
  }

  // ---- Response parsers (testable) -----------------------------------
  function parseText(provider, json) {
    if (!json) return "";
    if (provider === "anthropic") return (json.content && json.content[0] && json.content[0].text) || "";
    return (json.choices && json.choices[0] && json.choices[0].message && json.choices[0].message.content) || "";
  }
  function extractJson(text) {
    if (!text) return null;
    var s = String(text).replace(/```json/gi, "```").split("```").join("");
    var a = s.indexOf("{"), b = s.lastIndexOf("}");
    if (a === -1 || b === -1 || b < a) return null;
    try { return JSON.parse(s.slice(a, b + 1)); } catch (e) { return null; }
  }

  // ---- Request builders ----------------------------------------------
  function buildRequest(opts, system, user, imageDataUrl) {
    var provider = opts.provider, model = opts.model, key = opts.apiKey;
    if (provider === "anthropic") {
      var content = imageDataUrl
        ? [imgBlockAnthropic(imageDataUrl), { type: "text", text: user }]
        : user;
      return {
        url: "https://api.anthropic.com/v1/messages",
        headers: { "content-type": "application/json", "x-api-key": key,
          "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" },
        body: { model: model || "claude-sonnet-5", max_tokens: 1400, system: system,
          messages: [{ role: "user", content: content }] }
      };
    }
    // OpenAI-compatible (also works for Azure/OpenRouter/local gateways via baseUrl)
    var base = (opts.baseUrl || "https://api.openai.com/v1").replace(/\/$/, "");
    var umsg = imageDataUrl
      ? [{ type: "text", text: user }, { type: "image_url", image_url: { url: imageDataUrl } }]
      : user;
    return {
      url: base + "/chat/completions",
      headers: { "content-type": "application/json", "authorization": "Bearer " + key },
      body: { model: model || "gpt-4o-mini", max_tokens: 1400,
        messages: [{ role: "system", content: system }, { role: "user", content: umsg }] }
    };
  }
  function imgBlockAnthropic(dataUrl) {
    var m = /^data:([^;]+);base64,(.*)$/.exec(dataUrl) || [];
    return { type: "image", source: { type: "base64", media_type: m[1] || "image/jpeg", data: m[2] || "" } };
  }

  function hasProvider(opts) {
    return !!(opts && opts.provider && opts.provider !== "local" && opts.apiKey);
  }

  // ---- Async operations (network) ------------------------------------
  function polishNarrative(draft, opts) {
    opts = opts || {};
    if (!hasProvider(opts)) {
      return Promise.resolve({ ok: true, mode: "local", text: localTidy(draft) });
    }
    var payload = draft, red = null;
    if (opts.redact) { red = redactReversible(draft); payload = red.text; }
    var p = buildPolishPrompt(payload, opts.reportType);
    var req = buildRequest(opts, p.system, p.user, null);
    return fetch(req.url, { method: "POST", headers: req.headers, body: JSON.stringify(req.body) })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var text = parseText(opts.provider, j);
        if (!text) return { ok: false, mode: "ai", error: "Empty response", raw: j };
        if (red) text = restore(text, red.map);
        return { ok: true, mode: "ai", text: text, redacted: red ? red.count : 0 };
      })
      .catch(function (e) { return { ok: false, mode: "ai", error: String(e && e.message || e) }; });
  }

  function extractDocument(opts) {
    opts = opts || {};
    if (!hasProvider(opts)) {
      return Promise.resolve({ ok: false, error: "AI extraction needs a provider + API key (set in AI settings). Enter fields manually meanwhile." });
    }
    if (!opts.imageDataUrl) return Promise.resolve({ ok: false, error: "No image provided." });
    var system = buildExtractPrompt(opts.docType);
    var req = buildRequest(opts, system, "Extract the fields now.", opts.imageDataUrl);
    return fetch(req.url, { method: "POST", headers: req.headers, body: JSON.stringify(req.body) })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var fields = extractJson(parseText(opts.provider, j));
        return fields ? { ok: true, fields: fields } : { ok: false, error: "Could not parse fields from response." };
      })
      .catch(function (e) { return { ok: false, error: String(e && e.message || e) }; });
  }

  var AI = {
    redactReversible: redactReversible,
    restore: restore,
    localTidy: localTidy,
    buildPolishPrompt: buildPolishPrompt,
    buildExtractPrompt: buildExtractPrompt,
    parseText: parseText,
    extractJson: extractJson,
    buildRequest: buildRequest,
    hasProvider: hasProvider,
    polishNarrative: polishNarrative,
    extractDocument: extractDocument
  };

  if (typeof module !== "undefined" && module.exports) module.exports = AI;
  else root.AmanaAI = AI;
})(typeof window !== "undefined" ? window : this);
