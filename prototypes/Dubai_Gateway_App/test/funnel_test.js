var G=require("../funnel.js");var pass=0,fail=0;
function ok(n,c){if(c){pass++;console.log("  ✓ "+n);}else{fail++;console.log("  ✗ FAIL: "+n);}}

console.log("\n== ROI ==");
var r=G.calcROI({price:2700000,area:"Business Bay",appreciation:0.07,years:5});
ok("gross yield from area (6.6%)", Math.abs(r.grossYield-0.066)<1e-9);
ok("annual rent = price*yield", Math.round(r.annualRent)===Math.round(2700000*0.066));
ok("net < gross (mgmt cost applied)", r.netAnnual<r.annualRent);
ok("future value grows over 5y", r.futureValue>2700000);
ok("total profit positive", r.totalProfit>0);
ok("ROI includes golden visa (2.7M eligible)", r.goldenVisa.eligible===true && r.goldenVisa.tier.indexOf("10-Year")>=0);

console.log("\n== Golden Visa ==");
ok("2M+ -> 10-year golden", G.checkGoldenVisa(2000000).tier.indexOf("10-Year")>=0);
ok("1M -> 2-year investor + shortfall to 2M", G.checkGoldenVisa(1000000).tier.indexOf("2-Year")>=0 && G.checkGoldenVisa(1000000).shortfall===1000000);
ok("400k -> not eligible", G.checkGoldenVisa(400000).eligible===false);

console.log("\n== Lead qualification ==");
var hot=G.qualifyLead({budget:2500000,purpose:"Golden visa",timeline:"0-3 months",financing:"cash"});
ok("HNW visa cash 0-3mo => Hot + qualified", hot.tier==="Hot" && hot.qualified===true);
var cold=G.qualifyLead({budget:300000,purpose:"browsing",timeline:"12+ months",financing:"unsure"});
ok("low budget browser => Cold + not qualified", cold.tier==="Cold" && cold.qualified===false);
var warm=G.qualifyLead({budget:1500000,purpose:"investment",timeline:"3-6 months",financing:"mortgage"});
ok("mid investor => qualified", warm.qualified===true);

console.log("\n== Funnel economics (default scenario) ==");
var f=G.funnelModel({spend:30000,cpl:250,leadToQualified:0.25,qualifiedToClose:0.06,ticket:2700000,commissionPct:0.05});
ok("commission/deal = 135k", Math.round(f.commissionPerDeal)===135000);
ok("120 leads from 30k/250", Math.round(f.leads)===120);
ok("30 qualified", Math.round(f.qualified)===30);
ok("CPQL = AED 1,000", Math.round(f.cpql)===1000);
ok("break-even CPQL = 135k*6% = 8,100", Math.round(f.breakEvenCpql)===8100);
ok("headroom ~8.1x", Math.abs(f.headroom-8.1)<0.2);
ok("PROFITABLE verdict", f.profitable===true && /PROFITABLE/.test(f.verdict));
console.log("     -> "+f.verdict);
console.log("     revenue "+G.fmt.aed(f.revenue)+" | ROAS "+G.fmt.round(f.roas,1)+"x | CAC/deal "+G.fmt.aed(f.cacPerDeal));

console.log("\n== Funnel economics (bad scenario) ==");
var b=G.funnelModel({spend:50000,cpl:600,leadToQualified:0.10,qualifiedToClose:0.01,ticket:1500000,commissionPct:0.04});
ok("bad scenario -> not profitable", b.profitable===false && /NOT YET/.test(b.verdict));
console.log("     -> "+b.verdict);

console.log("\nRESULT: "+pass+" passed, "+fail+" failed");
process.exit(fail?1:0);
