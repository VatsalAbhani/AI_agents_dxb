const fs=require("fs");const {JSDOM}=require("jsdom");
let html=fs.readFileSync("index.html","utf8");
html=html.replace('<script src="funnel.js"></script>','<script>'+fs.readFileSync("funnel.js","utf8")+'</script>');
const dom=new JSDOM(html,{runScripts:"dangerously",url:"https://gw.local/"});const w=dom.window;
w.HTMLElement.prototype.scrollIntoView=function(){};w.scrollTo=function(){};
let pass=0,fail=0;const ok=(n,c)=>{c?(pass++,console.log("  ✓ "+n)):(fail++,console.log("  ✗ FAIL: "+n));};
const $=id=>w.document.getElementById(id);

ok("Gateway loaded",!!w.Gateway);
ok("3 project cards rendered",w.document.querySelectorAll("#projcards .pcard").length===3);
ok("area dropdown populated",$("roi_area").options.length>=6);
ok("ROI output rendered at init",/gross yield/.test($("roi_out").textContent));
ok("ROI shows golden visa line (2.7M)",/10-Year Golden Visa/.test($("roi_out").textContent));
ok("Visa output rendered at init",/Eligibility/.test($("visa_out").textContent));

// lead capture — hot lead
$("l_name").value="Rahul Mehta";$("l_email").value="r@x.com";$("l_country").value="India";
$("l_budget").value="2,500,000";
$("l_purpose").value="Golden Visa / residency";$("l_timeline").value="0-3 months (ready)";$("l_financing").value="Cash";
w.submitLead();
ok("thanks shown after submit",$("leadthanks").style.display==="block");
ok("qualified lead messaging",/great fit/i.test($("leadthanks").textContent));
ok("lead stored in localStorage",JSON.parse(w.localStorage.getItem("gateway_leads")).length===1);

// founder view
w.toggleView();
ok("founder view visible",$("founder").style.display==="block");
ok("verdict is profitable at defaults",/PROFITABLE/.test($("f_verdict").textContent)&&$("f_verdict").className.indexOf("good")>=0);
ok("CPQL metric present",/Cost \/ qualified lead/.test($("f_metrics").textContent));
ok("funnel bars rendered",w.document.querySelectorAll("#f_funnel .bar").length===3);

// push spend/close to bad scenario
$("s_cpl").value="800";$("s_q2c").value="1";$("s_ticket").value="500000";$("s_comm").value="2";w.runFunnel();
ok("verdict flips to NOT YET in bad scenario",/NOT YET/.test($("f_verdict").textContent)&&$("f_verdict").className.indexOf("bad")>=0);

// seed leads
w.seedLeads();
const rows=w.document.querySelectorAll("#leadrows tr").length;
ok("6 sample leads rendered",rows===6);
ok("lead summary shows qualified count",/qualified/.test($("lead_summary").textContent));

console.log("\nRESULT: "+pass+" passed, "+fail+" failed");process.exit(fail?1:0);
