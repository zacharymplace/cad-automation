// Receipt schema follows zcad.local_ci v1. No provenance is regenerated.
function validateReceipt(r) {
  if (!r || r.schema_version !== '1.0' || !['RUNNING','PASS','FAIL','ERROR','INTERRUPTED'].includes(r.status)) throw Error('Unsupported runner receipt.');
  if (r.gates !== undefined && !Array.isArray(r.gates)) throw Error('Invalid gate list.');
  for (const g of r.gates || []) {
    if (!g || typeof g.name !== 'string' || !['RUNNING','PASS','FAIL','ERROR','INTERRUPTED'].includes(g.status) || !Array.isArray(g.command) || !g.command.every(v=>typeof v==='string')) throw Error('Invalid gate record.');
  }
  for (const phase of ['repositories_before','repositories_after']) {
    if (r[phase] === undefined) continue;
    if (!r[phase] || typeof r[phase] !== 'object' || Array.isArray(r[phase])) throw Error('Invalid repository snapshots.');
    for (const s of Object.values(r[phase])) if (!s || typeof s.commit !== 'string' || typeof s.dirty !== 'boolean') throw Error('Invalid repository state.');
  }
  return r;
}
if (typeof module !== 'undefined') module.exports = {validateReceipt};
if (typeof document !== 'undefined' && !globalThis.ZcadHistoryPage) {
  const picker = document.createElement('label'); picker.className='file'; picker.textContent='Open runner folder';
  const input=document.createElement('input'); input.type='file'; input.multiple=true; input.setAttribute('webkitdirectory',''); picker.append(input);
  document.querySelector('.actions').prepend(picker);
  const panel=node('section',undefined,'panel'); panel.hidden=true; $('origin').after(panel);
  const oldReset=reset; reset=function(){oldReset();panel.hidden=true;panel.replaceChildren();};
  $('example').addEventListener('click',()=>{panel.hidden=true;panel.replaceChildren();});
  input.onchange=async()=>{
    const id=++loadId; reset();
    try {
      const files=Array.from(input.files); const receipts=files.filter(f=>f.name==='receipt.json');
      if(receipts.length!==1) throw Error('Choose one completed or checkpointed run folder containing receipt.json.');
      const rf=receipts[0], prefix=rf.webkitRelativePath.slice(0,-rf.name.length);
      const byName=new Map(files.filter(f=>f.webkitRelativePath.slice(0,-f.name.length)===prefix).map(f=>[f.name,f]));
      async function read(name){const f=byName.get(name);if(!f)throw Error(name+' is missing');if(f.size>10*1024*1024)throw Error(name+' exceeds 10 MiB');return f.text();}
      const raw=await read('receipt.json'), r=validateReceipt(JSON.parse(raw));
      const integrity=await verifyIntegrity(r,byName,async bytes=>{
        if(!globalThis.crypto?.subtle)throw Error('SHA-256 unavailable in this browser context');
        const hash=await crypto.subtle.digest('SHA-256',bytes);
        return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
      });
      let catalog, catalogError;try{catalog=ZcadModel.validate(JSON.parse(await read('catalog.json')));}catch(e){catalogError=e.message;}
      if(id!==loadId)return;
      if(catalog)load(catalog,'Runner catalog · '+rf.webkitRelativePath);
      panel.hidden=false; panel.append(node('h2','Local runner · recorded '+r.status));
      $('origin').textContent='Recorded execution-time evidence. Current repository state and freshness are unknown. Files remain in this tab.';
      panel.append(node('p','Started: '+(r.started_at??'Not recorded')+' · Finished: '+(r.finished_at??'Not recorded')+' · Exit code: '+(r.exit_code??'Not recorded')));
      panel.append(node('p',r.scope??'Scope not recorded'),node('p','Observed Git state changed: '+(r.observed_git_state_changed===undefined?'Not recorded':String(r.observed_git_state_changed))));
      const integrityPanel=node('div',undefined,'notice');
      integrityPanel.append(node('strong','Artifact integrity: '+integrity.status));
      for(const reason of integrity.reasons)integrityPanel.append(node('p',reason));
      if(integrity.status==='PASS')integrityPanel.append(node('p',integrity.file_count+' referenced files match the supplied receipt (SHA-256 and byte size).'));
      integrityPanel.append(node('p','Integrity is separate from gate success. Receipt authenticity and current repository state are unverified. Extra files are outside the binding. Browser file selection cannot check filesystem symlink metadata.'));
      panel.prepend(integrityPanel);
      if(integrity.status!=='PASS')$('origin').textContent+=' Artifact integrity: '+integrity.status+'; displayed catalog and logs are unverified.';
      for(const key of ['error','provenance_error','integrity_error'])if(r[key])panel.append(node('p',key+': '+r[key],'ERROR'));
      if(r.status==='PASS' && (!r.finished_at || r.exit_code!==0 || r.observed_git_state_changed!==false || !r.repositories_before || !r.repositories_after || !r.gates?.length || r.gates.some(g=>g.status!=='PASS')))panel.append(node('p','Receipt is incomplete or inconsistent with its recorded PASS.','ERROR'));
      panel.append(node('h2','Gate results'));
      const passing=node('details');passing.append(node('summary','Passing gates'));
      for(const g of [...(r.gates||[])].sort((a,b)=>(a.status==='PASS')-(b.status==='PASS'))){
        const box=node('div',undefined,'check');box.append(badge(g.status),node('strong',g.name),node('p','Exit code: '+(g.returncode??'Not recorded')),node('pre',JSON.stringify(g.command)));
        if(g.error)box.append(node('p',g.error));
        if(g.name==='catalog' && catalog){const jump=node('button','View catalog findings');jump.onclick=showCatalogFindings;box.append(jump);}
        for(const key of ['stdout','stderr'])if(typeof g[key]==='string'){
          const d=node('details');d.append(node('summary',key+': '+g[key]));
          const pre=node('pre','Expand to read log');d.append(pre);let loaded=false;
          d.ontoggle=async()=>{if(!d.open||loaded)return;loaded=true;try{pre.textContent=await read(g[key]);}catch(e){pre.textContent=e.message;}};box.append(d);
        }
        (g.status==='PASS'?passing:panel).append(box);
      }
      panel.append(passing,node('h2','Repository snapshots at execution time'));
      const table=node('table');table.style.cssText='width:100%;text-align:left;overflow-wrap:anywhere;table-layout:fixed';
      const head=node('tr');for(const s of ['Repository / snapshot','Commit SHA','Dirty state'])head.append(node('th',s));table.append(head);
      for(const phase of ['repositories_before','repositories_after']){
        if(!r[phase])panel.append(node('p',phase+': Not recorded'));
        for(const [name,s] of Object.entries(r[phase]||{})){
          const tr=node('tr');tr.append(node('td',name+' / '+phase.replace('repositories_','')),node('td',s.commit),node('td',s.dirty?'Dirty':'Clean'));table.append(tr);
        }
      }
      panel.append(table);
      const original=node('details');original.append(node('summary','Original receipt JSON · includes paths and porcelain state'),node('pre',raw));panel.append(original);
      if(catalogError)panel.append(node('p','Catalog unavailable or rejected: '+catalogError,'ERROR'));
      else {$('identity').prepend(node('p','Execution provenance is recorded in the runner panel above. Catalog JSON itself does not contain it.'));}
    }catch(e){if(id===loadId){reset();$('error').textContent='Runner bundle rejected: '+e.message;}}
    finally{input.value='';}
  };
}
