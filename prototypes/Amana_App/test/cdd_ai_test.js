var CDD=require("../cdd.js"), AI=require("../ai.js");
var pass=0,fail=0;
function ok(name,cond){ if(cond){pass++;console.log("  ✓ "+name);} else {fail++;console.log("  ✗ FAIL: "+name);} }

console.log("\n== UBO tracer ==");
// Gulf Trading LLC: 40% direct person (Sara), 60% Marina Holdings; Marina owned 60% Ahmed / 40% Lena
var subject={ name:"Gulf Trading LLC", kind:"entity", owners:[
  { name:"Sara Ali", kind:"person", percent:40, nationality:"AE", idNumber:"P111" },
  { name:"Marina Holdings", kind:"entity", percent:60, owners:[
     { name:"Ahmed Ben Salah", kind:"person", percent:60, nationality:"TN", idNumber:"P222" },
     { name:"Lena Cruz", kind:"person", percent:40, nationality:"PH", idNumber:"P333" }
  ]}
]};
var r=CDD.traceUBO(subject);
var ahmed=r.persons.find(function(p){return p.name==="Ahmed Ben Salah";});
var sara=r.persons.find(function(p){return p.name==="Sara Ali";});
var lena=r.persons.find(function(p){return p.name==="Lena Cruz";});
ok("Ahmed effective = 36% (60% of 60%)", ahmed.effective===36);
ok("Sara effective = 40% (direct)", sara.effective===40);
ok("Lena effective = 24% (40% of 60%)", lena.effective===24);
ok("UBOs are Sara(40) and Ahmed(36), not Lena(24)", r.ubos.length===2 && r.ubos.every(function(p){return p.effective>=25;}));
ok("hasUBO true", r.hasUBO===true);
ok("layers detected = 2", r.layers===2);
console.log("   UBO lines:"); r.ubos.forEach(function(p){console.log("     - "+CDD.describeUBO(p));});

// No-UBO case: four 25%... make them 24 each via an intermediate to force <25
var flat={ name:"Diffuse LLC", kind:"entity", owners:[
  {name:"A",kind:"person",percent:20},{name:"B",kind:"person",percent:20},
  {name:"C",kind:"person",percent:20},{name:"D",kind:"person",percent:20},{name:"E",kind:"person",percent:20}]};
var r2=CDD.traceUBO(flat);
ok("diffuse ownership -> no UBO", r2.hasUBO===false);
ok("diffuse -> fallback text present", typeof r2.fallback==="string" && /senior managing official/.test(r2.fallback));

console.log("\n== Risk engine ==");
ok("sanctions hit forces High", CDD.riskRate({sanctionsHit:true}).level==="High");
ok("sanctions hit -> freeze/STR action", /freeze/i.test(CDD.riskRate({sanctionsHit:true}).actions.join(" ")));
ok("pep+highrisk+unclearSOF -> High (6)", CDD.riskRate({pep:true,highRiskJurisdiction:true,unclearSOF:true}).level==="High");
ok("single cash-intensive -> Low", CDD.riskRate({cashIntensive:true}).level==="Low");
ok("pep+cash -> Medium (3)", CDD.riskRate({pep:true,cashIntensive:true}).level==="Medium");

console.log("\n== AI: redaction round-trip ==");
var txt="Contact mlro@skyline.ae, passport P1234567, EID 784-1985-1112223-1.";
var red=AI.redactReversible(txt);
ok("redaction removed email+id+eid (3)", red.count===3);
ok("redacted text hides originals", !/skyline\.ae/.test(red.text) && !/P1234567/.test(red.text) && !/784-1985/.test(red.text));
ok("restore round-trips exactly", AI.restore(red.text, red.map)===txt);

console.log("\n== AI: prompts + parsers ==");
var pp=AI.buildPolishPrompt("1. CONTEXT...","STR");
ok("polish prompt forbids inventing facts", /do NOT invent/i.test(pp.system));
ok("polish prompt preserves tokens", /⟦...⟧|tokens EXACTLY/i.test(pp.system));
ok("anthropic parse", AI.parseText("anthropic",{content:[{text:"hello"}]})==="hello");
ok("openai parse", AI.parseText("openai",{choices:[{message:{content:"hi"}}]})==="hi");
ok("extractJson from fenced", JSON.stringify(AI.extractJson("```json\n{\"fullName\":\"X\"}\n```")) === '{"fullName":"X"}');
ok("hasProvider false when local", AI.hasProvider({provider:"local"})===false);
ok("hasProvider true with key", AI.hasProvider({provider:"anthropic",apiKey:"k"})===true);
var req=AI.buildRequest({provider:"anthropic",apiKey:"k",model:"claude-sonnet-5"},"sys","usr",null);
ok("anthropic request has browser header", req.headers["anthropic-dangerous-direct-browser-access"]==="true");
ok("anthropic url correct", req.url==="https://api.anthropic.com/v1/messages");
var req2=AI.buildRequest({provider:"openai",apiKey:"k",baseUrl:"https://api.openai.com/v1"},"sys","usr",null);
ok("openai url correct", req2.url==="https://api.openai.com/v1/chat/completions");

console.log("\n== localTidy ==");
ok("tidy collapses blank lines", AI.localTidy("a\n\n\n\nb").indexOf("\n\n\n")===-1);

console.log("\nRESULT: "+pass+" passed, "+fail+" failed");
process.exit(fail?1:0);
