const fs=require("fs");const {JSDOM}=require("jsdom");
let html=fs.readFileSync("index.html","utf8");
["engine.js","cdd.js","ai.js"].forEach(function(f){html=html.replace('<script src="'+f+'"></script>','<script>'+fs.readFileSync(f,"utf8")+'</script>');});
const dom=new JSDOM(html,{runScripts:"dangerously",url:"https://amana.local/"});const w=dom.window;
w.HTMLElement.prototype.scrollIntoView=function(){};
let pass=0,fail=0;function ok(n,c){if(c){pass++;console.log("  ✓ "+n);}else{fail++;console.log("  ✗ FAIL: "+n);}}
const $=function(id){return w.document.getElementById(id);};

console.log("\n== libraries ==");
ok("AmanaEngine loaded",!!w.AmanaEngine);ok("AmanaCDD loaded",!!w.AmanaCDD);ok("AmanaAI loaded",!!w.AmanaAI);
ok("15 indicators rendered",w.document.querySelectorAll(".indicator").length===15);
ok("9 risk factors rendered",w.document.querySelectorAll(".rfactor").length===9);

console.log("\n== filing flow ==");
w.loadSample();
ok("narrative populated",$("narrative").value.length>400);
ok("xml populated + well-formed-ish",/^<\?xml/.test($("xmlraw").value));
ok("output panel visible",$("outpanel").style.display!=="none");

console.log("\n== AI polish (local/offline) ==");
return (async function(){
  await w.polish();
  await new Promise(r=>setTimeout(r,30));
  ok("narrative still present after tidy",$("narrative").value.length>400);
  ok("undo button shown after polish",$("undoBtn").style.display!=="none");

  console.log("\n== view switch ==");
  w.switchView("cdd");
  ok("cdd view visible",$("view-cdd").hidden===false);
  ok("filing view hidden",$("view-filing").hidden===true);

  console.log("\n== CDD / UBO flow ==");
  w.cddLoadSample();
  ok("owners rows rendered",w.document.querySelectorAll("#owners-host .orow").length>=3);
  const ubo=$("ubo-out").textContent;
  ok("UBO output mentions Ahmed",/Ahmed/.test(ubo));
  ok("UBO output shows 36%",/36%/.test(ubo));
  ok("UBO output shows Sara 40%",/Sara/.test(ubo)&&/40%/.test(ubo));
  ok("risk assessed (badge shown)",/risk-(Low|Medium|High)/.test($("risk-out").innerHTML));
  ok("CDD summary built",$("cddraw").value.indexOf("CDD SUMMARY")===0);

  console.log("\n== use-in-filing handoff ==");
  w.useInFiling();
  ok("filing subject name copied",$("s_name").value==="Gulf Trading LLC");
  ok("switched back to filing view",$("view-filing").hidden===false);

  console.log("\n== AI settings ==");
  w.switchView("ai");
  $("ai_provider").value="anthropic";$("ai_key").value="test-key";w.saveAI();
  const saved=JSON.parse(w.localStorage.getItem("amana_ai"));
  ok("AI settings persisted",saved.provider==="anthropic"&&saved.key==="test-key");

  console.log("\nRESULT: "+pass+" passed, "+fail+" failed");
  process.exit(fail?1:0);
})();
