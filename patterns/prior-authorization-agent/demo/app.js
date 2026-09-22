const REQUIRED = ["diagnosis","procedure_code","coverage","payer_policy"];
const CRITICAL_FLAGS = new Set(["missing_coverage","missing_policy","missing_patient","conflicting_identity","conflicting_policy","prompt_injection_detected"]);
const DECISION_CRITICAL_FIELDS = new Set(REQUIRED);
const MIN_FIELD_CONFIDENCE = 0.70;

const scenarios = [
  {
    id:"clean_mri", name:"Clean MRI request", description:"All required evidence is present, high-confidence and corroborated.",
    flags:[], evidence: REQUIRED.map(field=>({field,present:true,source_count:2,confidence: field==="procedure_code"?0.99:0.96}))
  },
  {
    id:"missing_coverage", name:"Missing coverage", description:"The clinical evidence is strong, but active coverage evidence is missing.",
    flags:["missing_coverage"], evidence: REQUIRED.map(field=>({field,present:field!=="coverage",source_count:field==="coverage"?0:2,confidence:field==="coverage"?0:0.96}))
  },
  {
    id:"conflicting_policy", name:"Conflicting payer policy", description:"Two policy sources disagree despite otherwise strong evidence.",
    flags:["conflicting_policy"], evidence: REQUIRED.map(field=>({field,present:true,source_count:2,confidence:0.95}))
  },
  {
    id:"prompt_injection", name:"Injected clinical note", description:"A note contains an instruction-like payload detected by the upstream sanitization layer.",
    flags:["prompt_injection_detected"], evidence: REQUIRED.map(field=>({field,present:true,source_count:2,confidence:0.97}))
  },
  {
    id:"weak_extraction", name:"Low-confidence extraction", description:"All fields are present, but one decision-critical extraction is below the confidence floor.",
    flags:[], evidence: REQUIRED.map(field=>({field,present:true,source_count:1,confidence:field==="diagnosis"?0.61:0.90}))
  }
];

const $ = id=>document.getElementById(id);
const select=$("scenarioSelect"), editor=$("evidenceEditor"), flagList=$("flagList");

function title(s){return s.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}

function renderScenario(index){
  const s=scenarios[index];
  $("scenarioDescription").textContent=s.description;
  editor.innerHTML="";
  s.evidence.forEach((item,i)=>{
    const row=document.createElement("div"); row.className="evidence-row";
    row.innerHTML=`
      <strong>${title(item.field)}</strong>
      <div><label>Present</label><div class="present-toggle"><input type="checkbox" data-i="${i}" data-k="present" ${item.present?"checked":""}></div></div>
      <div><label>Confidence</label><input type="number" min="0" max="1" step="0.01" data-i="${i}" data-k="confidence" value="${item.confidence}"></div>
      <div><label>Sources</label><input type="number" min="0" max="10" step="1" data-i="${i}" data-k="source_count" value="${item.source_count}"></div>`;
    editor.appendChild(row);
  });
  flagList.innerHTML="";
  [...CRITICAL_FLAGS].forEach(flag=>{
    const checked=s.flags.includes(flag);
    const label=document.createElement("label"); label.className="flag";
    label.innerHTML=`<input type="checkbox" value="${flag}" ${checked?"checked":""}> ${title(flag)}`;
    flagList.appendChild(label);
  });
  evaluate();
}

function readEvidence(){
  const base=scenarios[select.selectedIndex].evidence.map(x=>({...x}));
  editor.querySelectorAll("[data-i]").forEach(el=>{
    const i=Number(el.dataset.i), key=el.dataset.k;
    base[i][key]= key==="present" ? el.checked : Number(el.value);
  });
  return base;
}

function assess(evidence,required,flags,minScore){
  const byField=Object.fromEntries(evidence.filter(x=>x.field).map(x=>[x.field,x]));
  const missing=required.filter(f=>!(byField[f]||{}).present);
  const confidence=[], corroboration=[], lowConfidence=[];
  required.forEach(field=>{
    const item=byField[field]||{};
    if(!item.present) return;
    const c=Math.max(0,Math.min(1,Number(item.confidence)||0));
    confidence.push(c);
    if(c<MIN_FIELD_CONFIDENCE) lowConfidence.push(field);
    corroboration.push((Number(item.source_count)||0)>=2?1:0.5);
  });
  const completeness=required.length?(required.length-missing.length)/required.length:1;
  const meanConfidence=confidence.length?confidence.reduce((a,b)=>a+b,0)/confidence.length:0;
  const meanCorroboration=corroboration.length?corroboration.reduce((a,b)=>a+b,0)/corroboration.length:0;
  const score=Math.round((0.50*completeness+0.35*meanConfidence+0.15*meanCorroboration)*10000)/10000;
  const criticalMissing=missing.filter(x=>DECISION_CRITICAL_FIELDS.has(x)).sort();
  const criticalFlags=[...new Set(flags)].filter(x=>CRITICAL_FLAGS.has(x)).sort();
  const reasons=[];
  if(criticalMissing.length) reasons.push("Critical evidence missing: "+criticalMissing.join(", "));
  if(criticalFlags.length) reasons.push("Critical reliability flags: "+criticalFlags.join(", "));
  if(lowConfidence.length) reasons.push("Low-confidence critical evidence: "+[...lowConfidence].sort().join(", "));
  if(score<minScore) reasons.push(`Reliability score ${score.toFixed(2)} is below threshold ${minScore.toFixed(2)}`);
  const safe=!criticalMissing.length&&!criticalFlags.length&&!lowConfidence.length&&score>=minScore;
  if(safe) reasons.push("Evidence quality is sufficient for automated decisioning");
  return {safe_to_auto_decide:safe,score,reasons,missing_fields:missing,conflict_flags:[...new Set(flags)].sort(),
    metrics:{completeness,mean_confidence:meanConfidence,mean_corroboration:meanCorroboration,threshold:minScore}};
}

function evaluate(){
  const flags=[...flagList.querySelectorAll("input:checked")].map(x=>x.value);
  const threshold=Number($("threshold").value);
  const result=assess(readEvidence(),REQUIRED,flags,threshold);
  const pill=$("decisionPill");
  pill.className="decision "+(result.safe_to_auto_decide?"ok":"bad");
  pill.textContent=result.safe_to_auto_decide?"SAFE TO AUTO-DECIDE":"HUMAN REVIEW REQUIRED";
  $("scoreValue").textContent=result.score.toFixed(2);
  $("scoreBar").style.width=(result.score*100)+"%";
  $("completenessValue").textContent=(result.metrics.completeness*100).toFixed(0)+"%";
  $("confidenceValue").textContent=result.metrics.mean_confidence.toFixed(2);
  $("corroborationValue").textContent=result.metrics.mean_corroboration.toFixed(2);
  $("thresholdMetric").textContent=threshold.toFixed(2);
  $("reasonList").innerHTML=result.reasons.map(r=>"<li>"+r+"</li>").join("");
  $("jsonOutput").textContent=JSON.stringify(result,null,2);
}

scenarios.forEach((s,i)=>select.add(new Option(s.name,i)));
select.addEventListener("change",()=>renderScenario(select.selectedIndex));
$("evaluateBtn").addEventListener("click",evaluate);
$("threshold").addEventListener("input",e=>{$("thresholdValue").textContent=Number(e.target.value).toFixed(2); evaluate();});
$("copyBtn").addEventListener("click",async()=>{await navigator.clipboard.writeText($("jsonOutput").textContent); $("copyBtn").textContent="Copied"; setTimeout(()=>$("copyBtn").textContent="Copy JSON",1200);});
renderScenario(0);
