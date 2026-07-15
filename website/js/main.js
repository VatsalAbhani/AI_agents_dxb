/* ============================================================
   LEADCODE GUARD — motion & interaction
   Everything is progressive enhancement: with JS disabled the
   page is fully readable; GSAP only adds the choreography.
   ============================================================ */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var noanim = location.search.indexOf("noanim") !== -1;   // static render for QA/screenshots
  var hasGsap = typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined";
  var hasFx = hasGsap && !reduced && !noanim;

  if (hasGsap) gsap.registerPlugin(ScrollTrigger);

  /* ---------- hero: staggered line reveal ---------- */
  if (hasFx) {
    document.querySelectorAll(".hero__line").forEach(function (line) {
      var inner = document.createElement("span");
      inner.style.display = "inline-block";
      inner.innerHTML = line.innerHTML;
      line.innerHTML = "";
      line.appendChild(inner);
    });
    gsap.from(".hero__line > span", {
      yPercent: 110, duration: 1.15, ease: "power4.out", stagger: 0.13, delay: 0.15
    });
    gsap.from(".hero__eyebrow, .hero__sub, .hero__cta", {
      opacity: 0, y: 18, duration: 0.9, ease: "power3.out", stagger: 0.1, delay: 0.7
    });
  }

  /* ---------- generic reveals ---------- */
  if (hasFx) {
    document.querySelectorAll("[data-reveal]").forEach(function (el) {
      gsap.fromTo(el, { opacity: 0, y: 26 }, {
        opacity: 1, y: 0, duration: 0.9, ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 86%" }
      });
    });
    gsap.fromTo(".manifesto__title",
      { clipPath: "inset(0 0 100% 0)", y: 40 },
      { clipPath: "inset(0 0 0% 0)", y: 0, duration: 1.2, ease: "power4.out",
        scrollTrigger: { trigger: ".manifesto", start: "top 65%" } });
  }

  /* ============================================================
     THE THEATRE — one conversation through the Guard
     Deterministic renderer: render(step) rebuilds the exact state,
     so scrubbing back & forth can never desync.
     ============================================================ */
  var chatEl = document.getElementById("chat");
  var ledgerEl = document.getElementById("ledger");
  var trayEl = document.getElementById("tray");
  var sealEl = document.getElementById("seal");
  var captionEl = document.getElementById("caption");

  var LEAD_1 = "Saw your ad — looking for a 2-bed in Dubai Marina, budget around 2.4M.";
  var LEAD_2 = "Will I actually make money on it?";
  var DRAFT_OK = "Marina Vista fits — 2BR in Dubai Marina, AED 2.3M, ready. Shall I set up a viewing this week?";
  var DRAFT_BAD = "Guaranteed 20% appreciation — this is a 100% safe investment!";
  var DRAFT_FIX = "I can't promise returns — no one honestly can. But I'd gladly send recent Marina comparables so you can judge the numbers yourself.";

  function bubble(kind, text, meta) {
    var html = '<div class="bubble bubble--' + kind + '">' + text;
    if (meta) html += '<span class="bubble__meta">' + meta + "</span>";
    html += "</div>";
    return html;
  }
  function entry(text, cls) {
    return '<li class="ledger-entry' + (cls ? " " + cls : "") + '">' + text + "</li>";
  }

  // each step = full declarative state of the stage
  var STEPS = [
    { caption: "SCROLL ↓",
      chat: [], ledger: [], tray: "AGENT IDLE …", sealed: false },

    { caption: "A LEAD ARRIVES · RECORDED",
      chat: [bubble("lead", LEAD_1, "META ADS · 23:41")],
      ledger: [entry("#01 lead.received <i>→</i> <b>7b1e ✓</b>")],
      tray: "READING LEAD · QUALIFYING …", sealed: false },

    { caption: "THE AI DRAFTS · THE GATE CHECKS",
      chat: [bubble("lead", LEAD_1, "META ADS · 23:41")],
      ledger: [
        entry("#01 lead.received <i>→</i> <b>7b1e ✓</b>"),
        entry("#02 llm.draft <i>prev 7b1e →</i> <b>8f3a ✓</b>"),
        entry("#03 policy.check PASS <i>prev 8f3a →</i> <b>c17d ✓</b>")
      ],
      tray: 'DRAFT #1<span class="tray__draft">&ldquo;' + DRAFT_OK + '&rdquo;</span>' +
            '<span class="tray__chips"><span class="chip chip--ok">POLICY · PASS ✓</span>' +
            '<span class="chip">AWAITING APPROVAL …</span></span>',
      sealed: false },

    { caption: "A HUMAN APPROVES · ONLY THEN IT SENDS",
      chat: [
        bubble("lead", LEAD_1, "META ADS · 23:41"),
        bubble("agent", DRAFT_OK, "APPROVED BY MANAGER · SENT 23:43")
      ],
      ledger: [
        entry("#01 lead.received <i>→</i> <b>7b1e ✓</b>"),
        entry("#02 llm.draft <i>prev 7b1e →</i> <b>8f3a ✓</b>"),
        entry("#03 policy.check PASS <i>prev 8f3a →</i> <b>c17d ✓</b>"),
        entry("#04 approval by:manager <i>prev c17d →</i> <b>44b0 ✓</b>"),
        entry("#05 whatsapp.sent <i>prev 44b0 →</i> <b>9e2c ✓</b>")
      ],
      tray: "SENT ✓ · AGENT LISTENING …", sealed: false },

    { caption: "NOW — THE DANGEROUS QUESTION",
      chat: [
        bubble("lead", LEAD_1, "META ADS · 23:41"),
        bubble("agent", DRAFT_OK, "APPROVED BY MANAGER · SENT 23:43"),
        bubble("lead", LEAD_2, "23:47")
      ],
      ledger: [
        entry("#01 lead.received <i>→</i> <b>7b1e ✓</b>"),
        entry("#02 llm.draft <i>prev 7b1e →</i> <b>8f3a ✓</b>"),
        entry("#03 policy.check PASS <i>prev 8f3a →</i> <b>c17d ✓</b>"),
        entry("#04 approval by:manager <i>prev c17d →</i> <b>44b0 ✓</b>"),
        entry("#05 whatsapp.sent <i>prev 44b0 →</i> <b>9e2c ✓</b>"),
        entry("#06 lead.message <i>prev 9e2c →</i> <b>1a5d ✓</b>")
      ],
      tray: "DRAFTING REPLY …", sealed: false },

    { caption: "GUARD BLOCKS IT — BEFORE IT EXISTS ON A CUSTOMER'S PHONE",
      chat: [
        bubble("lead", LEAD_1, "META ADS · 23:41"),
        bubble("agent", DRAFT_OK, "APPROVED BY MANAGER · SENT 23:43"),
        bubble("lead", LEAD_2, "23:47"),
        '<div class="bubble bubble--blocked">' + DRAFT_BAD +
          '<span class="stamp">BLOCKED</span>' +
          '<span class="bubble__meta">NEVER SENT · POLICY: NO GUARANTEED RETURNS</span></div>'
      ],
      ledger: [
        entry("#01 lead.received <i>→</i> <b>7b1e ✓</b>"),
        entry("#02 llm.draft <i>prev 7b1e →</i> <b>8f3a ✓</b>"),
        entry("#03 policy.check PASS <i>prev 8f3a →</i> <b>c17d ✓</b>"),
        entry("#04 approval by:manager <i>prev c17d →</i> <b>44b0 ✓</b>"),
        entry("#05 whatsapp.sent <i>prev 44b0 →</i> <b>9e2c ✓</b>"),
        entry("#06 lead.message <i>prev 9e2c →</i> <b>1a5d ✓</b>"),
        entry("#07 policy.check <b>BLOCK ✗</b> <i>no-guaranteed-returns</i>", "ledger-entry--block")
      ],
      tray: '<span class="tray__chips"><span class="chip chip--block">BLOCKED ✗ GUARANTEED RETURNS</span>' +
            '<span class="chip">REQUESTING COMPLIANT REWRITE …</span></span>',
      sealed: false },

    { caption: "COMPLIANT REWRITE · APPROVED · SENT",
      chat: [
        bubble("lead", LEAD_1, "META ADS · 23:41"),
        bubble("agent", DRAFT_OK, "APPROVED BY MANAGER · SENT 23:43"),
        bubble("lead", LEAD_2, "23:47"),
        '<div class="bubble bubble--blocked">' + DRAFT_BAD +
          '<span class="stamp">BLOCKED</span>' +
          '<span class="bubble__meta">NEVER SENT · POLICY: NO GUARANTEED RETURNS</span></div>',
        bubble("agent", DRAFT_FIX, "REWRITE · APPROVED BY MANAGER · SENT 23:49")
      ],
      ledger: [
        entry("#05 whatsapp.sent <i>prev 44b0 →</i> <b>9e2c ✓</b>"),
        entry("#06 lead.message <i>prev 9e2c →</i> <b>1a5d ✓</b>"),
        entry("#07 policy.check <b>BLOCK ✗</b> <i>no-guaranteed-returns</i>", "ledger-entry--block"),
        entry("#08 remediation.redraft <i>prev e881 →</i> <b>b2c4 ✓</b>"),
        entry("#09 approval by:manager <i>prev b2c4 →</i> <b>d90a ✓</b>"),
        entry("#10 whatsapp.sent <i>prev d90a →</i> <b>f3e7 ✓</b>")
      ],
      tray: "SENT ✓ · CONVERSATION CONTINUES …", sealed: false },

    { caption: "THE WHOLE RUN — SEALED, VERIFIABLE BY ANYONE",
      chat: [
        bubble("lead", LEAD_1, "META ADS · 23:41"),
        bubble("agent", DRAFT_OK, "APPROVED BY MANAGER · SENT 23:43"),
        bubble("lead", LEAD_2, "23:47"),
        '<div class="bubble bubble--blocked">' + DRAFT_BAD +
          '<span class="stamp">BLOCKED</span>' +
          '<span class="bubble__meta">NEVER SENT · POLICY: NO GUARANTEED RETURNS</span></div>',
        bubble("agent", DRAFT_FIX, "REWRITE · APPROVED BY MANAGER · SENT 23:49")
      ],
      ledger: [
        entry("#06 lead.message <i>prev 9e2c →</i> <b>1a5d ✓</b>"),
        entry("#07 policy.check <b>BLOCK ✗</b> <i>no-guaranteed-returns</i>", "ledger-entry--block"),
        entry("#08 remediation.redraft <i>prev e881 →</i> <b>b2c4 ✓</b>"),
        entry("#09 approval by:manager <i>prev b2c4 →</i> <b>d90a ✓</b>"),
        entry("#10 whatsapp.sent <i>prev d90a →</i> <b>f3e7 ✓</b>"),
        entry("#11 run.sealed <i>merkle</i> <b>a3f9 ✓</b>")
      ],
      tray: "RUN COMPLETE ✓",
      sealed: true }
  ];

  var currentStep = -1;
  function render(step) {
    if (step === currentStep || !chatEl) return;
    currentStep = step;
    var s = STEPS[step];
    chatEl.innerHTML = s.chat.join("");
    ledgerEl.innerHTML = s.ledger.join("");
    trayEl.innerHTML = s.tray;
    captionEl.textContent = s.caption;
    sealEl.textContent = s.sealed ? "RUN SEALED · MERKLE a3f9 · INTACT ✓" : "— RECORDING · UNSEALED —";
    sealEl.classList.toggle("sealed", s.sealed);
    if (hasFx) {
      var latestChat = chatEl.lastElementChild;
      var latestLedger = ledgerEl.lastElementChild;
      if (latestChat) gsap.from(latestChat, { opacity: 0, y: 14, duration: 0.45, ease: "power2.out" });
      if (latestLedger) gsap.from(latestLedger, { opacity: 0, x: -10, duration: 0.4, ease: "power2.out" });
    }
  }
  render(0);

  var isDesktop = window.matchMedia("(min-width: 961px)").matches;
  if (chatEl && hasFx && isDesktop) {
    ScrollTrigger.create({
      trigger: "#theatre",
      start: "top 12%",
      end: "+=" + STEPS.length * 420,
      pin: true,
      onUpdate: function (self) {
        var step = Math.min(STEPS.length - 1, Math.floor(self.progress * STEPS.length));
        render(step);
      }
    });
  } else if (chatEl && !noanim) {
    // mobile / no-GSAP: auto-play once when the theatre becomes visible
    var played = false;
    var io = new IntersectionObserver(function (entries) {
      if (played || !entries[0].isIntersecting) return;
      played = true;
      io.disconnect();
      var i = 0;
      var t = setInterval(function () {
        i += 1;
        render(i);
        if (i >= STEPS.length - 1) clearInterval(t);
      }, reduced ? 60 : 1500);
    }, { threshold: 0.35 });
    io.observe(chatEl);
  }

  /* ============================================================
     THE TAMPER WIDGET — click an entry, break the chain
     ============================================================ */
  var chainEl = document.getElementById("chain");
  var verdictStatus = document.querySelector(".tamper__status");
  var restoreBtn = document.getElementById("restore");

  // hash = sealed value · fhash = recomputed after forging this entry
  // chash = recomputed downstream value once the break cascades through
  var ENTRIES = [
    { seq: "#01", type: "lead.received", text: "“Looking for a 2-bed in Marina, budget 2.4M.”",
      hash: "7b1e", prev: "0000",
      forged: "“Looking to invest my life savings, anything works.”", fhash: "c2a9", chash: "61f4" },
    { seq: "#02", type: "llm.draft", text: "“Marina Vista — 2BR, AED 2.3M, ready. Viewing this week?”",
      hash: "8f3a", prev: "7b1e",
      forged: "“Guaranteed 20% ROI — 100% safe. Sign today!”", fhash: "e77c", chash: "b905" },
    { seq: "#03", type: "approval", text: "Approved by manager · no edits · 23:43",
      hash: "44b0", prev: "8f3a",
      forged: "Approved by — nobody. Record erased.", fhash: "0dd1", chash: "27ce" },
    { seq: "#04", type: "whatsapp.sent", text: "Delivered to lead · 23:43:12",
      hash: "9e2c", prev: "44b0",
      forged: "Never sent. Nothing happened here.", fhash: "5b68", chash: "f81a" }
  ];

  function recomputed(i, forgedIdx) {
    if (forgedIdx === null || i < forgedIdx) return ENTRIES[i].hash;
    return i === forgedIdx ? ENTRIES[i].fhash : ENTRIES[i].chash;
  }

  function drawChain(forgedIdx) {
    if (!chainEl) return;
    chainEl.innerHTML = ENTRIES.map(function (e, i) {
      var cls = "tcard";
      var text = e.text, mark = "✓";
      if (forgedIdx !== null) {
        if (i === forgedIdx) { cls += " forged"; text = e.forged; mark = "✗"; }
        else if (i > forgedIdx) { cls += " broken"; mark = "✗"; }
      }
      // the break cascades: every downstream entry's stored prev-pointer no
      // longer matches the recomputed hash of the entry before it
      var mismatch = forgedIdx !== null && i > forgedIdx
        ? "stored prev <b>" + e.prev + "</b> · recomputed <b>" + recomputed(i - 1, forgedIdx) + "</b> " + mark
        : "prev <b>" + e.prev + "</b> → self <b>" + recomputed(i, forgedIdx) + "</b> " + mark;
      return (
        '<div class="' + cls + '" data-i="' + i + '" role="button" tabindex="0" ' +
        'aria-label="Forge ledger entry ' + e.seq + '">' +
        '<p class="tcard__seq">' + e.seq + " / RUN #0147</p>" +
        '<p class="tcard__type">' + e.type + "</p>" +
        '<p class="tcard__text">' + text + "</p>" +
        '<p class="tcard__hash">' + mismatch + "</p>" +
        '<span class="tcard__link">' + (forgedIdx !== null && i >= forgedIdx ? "✗" : "→") + "</span>" +
        "</div>"
      );
    }).join("");
  }

  function setVerdict(forgedIdx) {
    if (!verdictStatus) return;
    if (forgedIdx === null) {
      verdictStatus.textContent = "CHAIN VERIFIED · INTACT ✓";
      verdictStatus.className = "tamper__status ok";
      restoreBtn.hidden = true;
    } else {
      verdictStatus.textContent = "TAMPER DETECTED · CHAIN BROKEN AT " + ENTRIES[forgedIdx].seq + " ✗";
      verdictStatus.className = "tamper__status bad";
      restoreBtn.hidden = false;
    }
  }

  if (chainEl) {
    drawChain(null);
    chainEl.addEventListener("click", function (e) {
      var card = e.target.closest(".tcard");
      if (!card) return;
      var i = parseInt(card.getAttribute("data-i"), 10);
      drawChain(i);
      setVerdict(i);
    });
    chainEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var card = e.target.closest(".tcard");
      if (!card) return;
      e.preventDefault();
      var i = parseInt(card.getAttribute("data-i"), 10);
      drawChain(i);
      setVerdict(i);
    });
    restoreBtn.addEventListener("click", function () {
      drawChain(null);
      setVerdict(null);
    });
  }

  // QA/debug handle (harmless in production)
  window.__guard = { render: render, steps: STEPS.length, drawChain: drawChain, setVerdict: setVerdict };
})();
