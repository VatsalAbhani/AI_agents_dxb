// Node test harness for the Amana goAML engine.
// Run: node test/sample_run.js  (from the Amana_App folder)
var E = require("../engine.js");
var fs = require("fs");
var path = require("path");

function line() { console.log("\n" + "=".repeat(72) + "\n"); }

// ---- Sample 1: STR — real-estate brokerage, suspicious cash villa buyer ----
var strCase = {
  reportType: "STR",
  entity: { name: "Skyline Properties LLC", type: "Real-estate brokerage", licenseNo: "CN-1234567",
            mlroName: "Rana Haddad", mlroEmail: "mlro@skyline.ae", rentityId: "778812", emirate: "Dubai" },
  subject: { kind: "person", fullName: "John A. Doe", nationality: "Country X", idType: "Passport",
             idNumber: "P1234567", dob: "1980-05-02", address: "Marina Tower, Dubai" },
  txn: { date: "2026-07-03", amount: "6000000", currency: "AED", method: "cash",
         direction: "incoming", counterparty: "Third-party account (unrelated)" },
  indicators: ["STR-STRUCT", "STR-3RDPARTY", "STR-SOF", "STR-PEP"],
  grounds: "Buyer insisted on paying AED 6,000,000 largely in cash routed through an unrelated third party and could not evidence source of funds.",
  screening: { pep: "yes", sanctions: "no" },
  action: "Transaction placed on hold; relationship under enhanced review pending FIU guidance.",
  preparedBy: "Rana Haddad"
};

// ---- Sample 2: REAR — cash property deal above threshold ----
var rearCase = {
  reportType: "REAR",
  entity: { name: "Skyline Properties LLC", type: "Real-estate brokerage", licenseNo: "CN-1234567",
            mlroName: "Rana Haddad", mlroEmail: "mlro@skyline.ae", rentityId: "778812", emirate: "Dubai" },
  subject: { kind: "entity", fullName: "Gulf Trading LLC", tradeLicense: "DED-99887",
             address: "Business Bay, Dubai", uboName: "Ahmed Ben Salah", uboNationality: "Country Y", uboIdNumber: "784-1985-1112223-1" },
  txn: { date: "2026-07-01", amount: "2200000", currency: "AED", method: "cash",
         direction: "incoming", counterparty: "Gulf Trading LLC", propertyRef: "Freehold Villa, Palm Jumeirah — Plot 12" }
};

// ---- Sample 3: DPMSR — below threshold (should warn) ----
var dpmsrCase = {
  reportType: "DPMSR",
  entity: { name: "Deira Gold House", type: "Precious-metals dealer", licenseNo: "CN-5566778",
            mlroName: "Karim Nasser", mlroEmail: "mlro@deiragold.ae", rentityId: "551234", emirate: "Dubai" },
  subject: { kind: "person", fullName: "Walk-in Buyer", nationality: "Country Z", idType: "Emirates ID",
             idNumber: "784-1990-0000000-1", dob: "1990-01-01", address: "Deira, Dubai" },
  txn: { date: "2026-07-05", amount: "40000", currency: "AED", method: "cash",
         direction: "incoming", counterparty: "Walk-in Buyer", goodsDesc: "1kg gold bars x2" }
};

var cases = { STR: strCase, REAR: rearCase, DPMSR: dpmsrCase };
var outDir = path.join(__dirname, "output");
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

Object.keys(cases).forEach(function (k) {
  var d = cases[k];
  line();
  console.log(">>> " + k + " CASE");
  var v = E.validate(d);
  console.log("valid:", v.ok, "| errors:", v.errors.length, "| warnings:", v.warnings.length);
  if (v.errors.length) console.log("  errors:", v.errors);
  if (v.warnings.length) console.log("  warnings:", v.warnings);
  console.log("  threshold:", v.threshold.triggered ? "TRIGGERED" : "not triggered", "-", v.threshold.note);
  console.log("  deadline:", v.deadline);
  var narr = E.buildNarrative(d);
  var xml = E.buildGoAmlXml(d);
  fs.writeFileSync(path.join(outDir, k + "_narrative.txt"), narr);
  fs.writeFileSync(path.join(outDir, k + "_goaml.xml"), xml);
  console.log("  narrative chars:", narr.length, "| xml chars:", xml.length);
});

line();
console.log("Wrote narratives + XML to:", outDir);
console.log("Preview — STR narrative:\n");
console.log(E.buildNarrative(strCase));
