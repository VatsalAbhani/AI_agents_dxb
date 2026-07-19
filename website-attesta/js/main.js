/* ============================================================
   ATTESTA — motion & interaction
   Progressive enhancement only: with JS off the page reads
   complete (verifier shows its final verified state via noanim
   rules below). ?noanim renders everything final for QA.
   ============================================================ */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var noanim = location.search.indexOf("noanim") !== -1;
  var hasGsap = typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined";
  var hasFx = hasGsap && !reduced && !noanim;

  if (hasGsap) gsap.registerPlugin(ScrollTrigger);

  var HEX = "0123456789abcdef";

  function randHex(n) {
    var s = "";
    for (var i = 0; i < n; i++) s += HEX[Math.floor(Math.random() * 16)];
    return s;
  }

  /* ---------- the self-verifying ledger (hero) ---------- */
  var list = document.getElementById("v-list");
  var seal = document.getElementById("v-seal");
  var status = document.getElementById("v-status");

  function verifyFinalState() {
    if (!list) return;
    Array.prototype.forEach.call(list.children, function (li) {
      li.classList.add("done");
      li.querySelector("b.h").textContent = li.getAttribute("data-hash");
      li.querySelector("u").textContent = "✓";
    });
    if (seal) seal.classList.add("stamped");
    if (status) status.textContent = "VERIFIED";
  }

  function verifyAnimated() {
    var lines = Array.prototype.slice.call(list.children);
    var lineDur = 420, scrambleEvery = 45;

    function runLine(idx) {
      if (idx >= lines.length) {
        status.textContent = "VERIFIED";
        seal.classList.add("stamped");
        if (hasGsap) {
          gsap.fromTo(seal, { scale: 0.96 }, { scale: 1, duration: 0.35, ease: "back.out(3)" });
        }
        return;
      }
      var li = lines[idx];
      var hashEl = li.querySelector("b.h");
      var target = li.getAttribute("data-hash");
      var t0 = performance.now();
      var scrambler = setInterval(function () {
        if (performance.now() - t0 >= lineDur) {
          clearInterval(scrambler);
          hashEl.textContent = target;
          li.classList.add("done");
          li.querySelector("u").textContent = "✓";
          runLine(idx + 1);
        } else {
          hashEl.textContent = randHex(4);
        }
      }, scrambleEvery);
    }
    runLine(0);
  }

  if (list && seal && status) {
    if (!hasFx) verifyFinalState();
    else setTimeout(verifyAnimated, 500);
  }

  /* ---------- hero text entrance ---------- */
  if (hasFx) {
    gsap.from(".hero__title span", {
      opacity: 0, y: 22, duration: 0.7, ease: "power3.out", stagger: 0.1, delay: 0.1
    });
    gsap.from(".eyebrow, .hero__sub, .hero__cta", {
      opacity: 0, y: 14, duration: 0.7, ease: "power3.out", stagger: 0.1, delay: 0.45
    });
    gsap.from(".verifier", {
      opacity: 0, x: 24, duration: 0.8, ease: "power3.out", delay: 0.3
    });
  }

  /* ---------- generic reveals ---------- */
  if (hasFx) {
    document.querySelectorAll("[data-reveal]").forEach(function (el) {
      gsap.fromTo(el, { opacity: 0, y: 22 }, {
        opacity: 1, y: 0, duration: 0.8, ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%" }
      });
    });
  }

  /* ---------- terminal typing (§03) ---------- */
  var term = document.getElementById("term");
  if (term) {
    var linesData = [];
    try { linesData = JSON.parse(term.getAttribute("data-lines")) || []; } catch (e) { /* noop */ }
    var codeEl = term.querySelector("code");
    var cursor = term.querySelector(".term__cursor");

    function termFinal() {
      codeEl.textContent = linesData.join("\n");
      if (cursor) cursor.style.display = "none";
    }

    function typeTerm() {
      var li = 0, ci = 0, out = "";
      function tick() {
        if (li >= linesData.length) { if (cursor) cursor.style.display = "none"; return; }
        var line = linesData[li];
        var isCmd = line.charAt(0) === "$";
        if (ci < line.length) {
          out += line.charAt(ci);
          ci += 1;
          codeEl.textContent = out;
          setTimeout(tick, isCmd ? 42 : 8);
        } else {
          out += "\n";
          li += 1; ci = 0;
          codeEl.textContent = out;
          setTimeout(tick, isCmd ? 500 : 140);
        }
      }
      tick();
    }

    if (!hasFx) termFinal();
    else {
      var played = false;
      ScrollTrigger.create({
        trigger: term, start: "top 80%",
        onEnter: function () { if (!played) { played = true; typeTerm(); } }
      });
    }
  }

  // QA hook
  window.__attesta = { verifyFinalState: verifyFinalState };
})();
