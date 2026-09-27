// Comparisons describe recorded evidence only; neither input is rewritten.
(function(root){
  function stable(value){
    if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
    if(value && typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
    return JSON.stringify(value);
  }
  function changes(left,right,key){
    const group=items=>{const m=new Map();for(const item of items){const k=key(item);if(!m.has(k))m.set(k,[]);m.get(k).push(item);}return m;};
    const a=group(left),b=group(right);
    return [...new Set([...a.keys(),...b.keys()])].map(k=>{
      const before=a.get(k)||[],after=b.get(k)||[];
      const ambiguous=before.length>1||after.length>1;
      const same=stable(before)===stable(after);
      return {key:k,before,after,kind:ambiguous?'Ambiguous identity':!before.length?'Added':!after.length?'Removed':same?'Unchanged':'Changed'};
    });
  }
  function compareRuns(a,b){
    const gates=changes(a.receipt.gates||[],b.receipt.gates||[],g=>g.name);
    const designs=a.catalog&&b.catalog?changes(a.catalog.results,b.catalog.results,r=>r.path):null;
    return {gates,designs,policyChanged:a.catalog&&b.catalog?stable(a.catalog.policy)!==stable(b.catalog.policy):null};
  }
  function findings(a,b){return changes(a?.report?.checks||[],b?.report?.checks||[],c=>JSON.stringify([c.code,c.part_name??null]));}
  async function readBundle(files,validateReceipt,validateCatalog,verify,digest){
    const list=Array.from(files),receipts=list.filter(f=>f.name==='receipt.json');
    if(receipts.length!==1)throw Error('Select exactly one run folder containing receipt.json.');
    const rf=receipts[0],prefix=rf.webkitRelativePath.slice(0,-rf.name.length),map=new Map();
    for(const f of list.filter(f=>f.webkitRelativePath.slice(0,-f.name.length)===prefix)){
      if(map.has(f.name))throw Error('Duplicate filename: '+f.name);map.set(f.name,f);
    }
    async function read(name){const f=map.get(name);if(!f)throw Error(name+' is missing');if(f.size>10*1024*1024)throw Error(name+' exceeds 10 MiB');return f.text();}
    const raw=await read('receipt.json'),receipt=validateReceipt(JSON.parse(raw));
    if(!['PASS','FAIL','ERROR','INTERRUPTED'].includes(receipt.status)||typeof receipt.finished_at!=='string'||!Number.isFinite(Date.parse(receipt.finished_at)))throw Error('A completed run with a valid finished_at is required.');
    const integrity=await verify(receipt,map,digest);
    let catalog=null,catalogError=null;
    try{catalog=validateCatalog(JSON.parse(await read('catalog.json')));}catch(e){catalogError=e.message;}
    return {receipt,raw,integrity,catalog,catalogError,label:prefix||rf.name};
  }
  root.ZcadCompare={compareRuns,findings,readBundle};
  if(typeof module!=='undefined')module.exports=root.ZcadCompare;
})(globalThis);

if(typeof document!=='undefined'){
  const section=node('section',undefined,'panel');section.style.marginTop='24px';
  section.append(node('h2','Compare completed runs'),node('p','Choose baseline A and comparison B. Order is your choice, not inferred chronology. Changes describe recorded evidence; they do not establish cause or current repository state.','muted'));
  const controls=node('div',undefined,'actions'),cards=node('div',undefined,'comparison-cards'),output=node('div');
  section.append(controls,cards,output);document.querySelector('footer').before(section);
  const runs=[null,null],versions=[0,0],slots=[];
  const digest=async bytes=>{if(!globalThis.crypto?.subtle)throw Error('SHA-256 unavailable');const hash=await crypto.subtle.digest('SHA-256',bytes);return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');};
  function evidence(title,value){const d=node('details');d.append(node('summary',title),node('pre',typeof value==='string'?value:JSON.stringify(value,null,2)));return d;}
  function showCard(i,run){const card=slots[i];card.replaceChildren(node('h3',i?'Comparison B':'Baseline A'),node('p',run.label),node('p','Recorded run: '+run.receipt.status),node('p','Artifact integrity: '+run.integrity.status));
    card.append(node('p','Started: '+(run.receipt.started_at??'Not recorded')+' · Finished: '+run.receipt.finished_at),node('p','Exit: '+(run.receipt.exit_code??'Not recorded')));
    if(run.integrity.status==='PASS')card.append(node('p',run.integrity.file_count+' referenced files match.'));
    for(const reason of run.integrity.reasons||[])card.append(node('p',reason));
    card.append(node('p','Integrity checks artifact bytes, independently of gate success.','muted'),evidence('Integrity scope & limits','Receipt authenticity and current repository state are unverified. Extra files are outside the binding; browser selection cannot check symlink metadata.'));
    for(const phase of ['repositories_before','repositories_after'])card.append(evidence(phase.replaceAll('_',' '),run.receipt[phase]??'Not recorded'));
    card.append(evidence('Original receipt JSON',run.raw));
    if(run.catalogError)card.append(node('p','Catalog unavailable: '+run.catalogError,'ERROR'));
  }
  function table(title,rows,label){
    const wrap=node('div',undefined,'table-wrap'),t=node('table');t.append(node('caption',title));
    const h=node('tr');for(const s of ['Identity','Change','Baseline A','Comparison B']){const th=node('th',s);th.scope='col';h.append(th);}const head=node('thead');head.append(h);t.append(head);
    const body=node('tbody');for(const r of rows){const tr=node('tr');tr.append(node('td',r.key),node('td',r.kind),node('td',r.before.length?r.before.map(label).join(' | '):'Not present'),node('td',r.after.length?r.after.map(label).join(' | '):'Not present'));body.append(tr);}t.append(body);wrap.append(t);return wrap;
  }
  function renderComparison(){output.replaceChildren();if(!runs.every(Boolean)){output.append(node('p','Load both completed runs to compare.'));return;}
    const result=ZcadCompare.compareRuns(...runs);
    if(runs.some(r=>r.integrity.status!=='PASS'))output.append(node('p','At least one run is unbound or has an integrity problem. Treat these differences as unverified.','notice'));
    output.append(node('p','Gates match by name; designs by exact path. Renamed designs appear as added and removed. Removed checks are not evidence of a fix. Duplicate identities are marked ambiguous.','muted'));
    const changed=result.gates.filter(r=>r.kind!=='Unchanged');output.append(table('Gate changes ('+changed.length+')',changed,g=>g.status+' · exit '+(g.returncode??'not recorded')));
    for(const r of changed)output.append(evidence('Gate evidence: '+r.key,{baseline:r.before,comparison:r.after}));
    const same=node('details');same.append(node('summary','Unchanged gates'),table('Unchanged gate records',result.gates.filter(r=>r.kind==='Unchanged'),g=>g.status));output.append(same);
    if(!result.designs){output.append(node('p','Design comparison unavailable: both valid catalogs are required.','notice'));return;}
    if(result.policyChanged)output.append(node('p','Reported catalog policy differs; outcomes may not be directly comparable.','notice'),evidence('Catalog policies',{baseline:runs[0].catalog.policy??null,comparison:runs[1].catalog.policy??null}));
    const designs=result.designs.filter(r=>r.kind!=='Unchanged');output.append(table('Design changes ('+designs.length+')',designs,r=>r.status));
    for(const r of designs){const d=node('details');d.append(node('summary',r.key+' · '+r.kind));
      const findings=ZcadCompare.findings(r.before[0],r.after[0]).filter(c=>c.kind!=='Unchanged');
      d.append(table('Changed checks',findings,c=>c.status+(c.message?' · '+c.message:'')));
      for(const f of findings)d.append(evidence('Check evidence: '+f.key,{baseline:f.before,comparison:f.after}));
      d.append(evidence('Complete design evidence (includes policy, coverage and dimensions)',{baseline:r.before,comparison:r.after}));output.append(d);
    }
    output.append(node('p',result.designs.filter(r=>r.kind==='Unchanged').length+' unchanged designs.'));
  }
  for(let i=0;i<2;i++){
    const card=node('div');slots.push(card);cards.append(card);
    const label=node('label',i?'Open comparison B':'Open baseline A','file'),input=document.createElement('input');input.type='file';input.multiple=true;input.setAttribute('webkitdirectory','');label.append(input);controls.append(label);
    input.onchange=async()=>{if(!input.files.length)return;const version=++versions[i];runs[i]=null;card.replaceChildren(node('p','Reading '+(i?'comparison B':'baseline A')+'…'));renderComparison();try{
      const run=await ZcadCompare.readBundle(input.files,validateReceipt,ZcadModel.validate,verifyIntegrity,digest);
      if(version!==versions[i])return;runs[i]=run;showCard(i,run);renderComparison();
    }catch(e){if(version===versions[i]){card.replaceChildren(node('p',e.message,'ERROR'));renderComparison();}}finally{input.value='';}};
  }
  const clear=node('button','Clear comparison');clear.onclick=()=>{for(let i=0;i<2;i++){versions[i]++;runs[i]=null;slots[i].replaceChildren();}renderComparison();};controls.append(clear);$('clear').addEventListener('click',()=>clear.onclick());renderComparison();
}
