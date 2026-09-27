const sampleRuns=[
{id:'sample-06',finish:'2026-09-27T03:30:00Z',status:'ERROR',gates:'5/5 PASS; repository changed',integrity:'Not checked',completed:true,sha:'sample-sha-f',dirty:true,note:'Sample: all gates passed, but observed repository state changed during execution.'},
{id:'sample-05',finish:'2026-09-27T03:20:00Z',status:'FAIL',gates:'catalog FAIL',integrity:'Not checked',completed:true,sha:'sample-sha-e',dirty:false,note:'Sample: catalog reports a failing dimension check.'},
{id:'sample-04',finish:'2026-09-27T03:10:00Z',status:'PASS',gates:'5/5 PASS',integrity:'Not checked',completed:true,sha:'sample-sha-d',dirty:false,note:'Sample: passing gates. Artifact hashes have not been checked.'},
{id:'sample-03',finish:'2026-09-27T03:00:00Z',status:'PASS',gates:'5/5 PASS',integrity:'FAIL (simulated)',completed:true,sha:'sample-sha-c',dirty:false,note:'Sample: recorded PASS, but a simulated changed artifact makes its evidence unverified.'},
{id:'sample-02',finish:null,status:'RUNNING',gates:'tests RUNNING',integrity:'Not checked',completed:false,sha:'sample-sha-b',dirty:false,note:'Sample checkpoint, not proof the process is still alive. No completed receipt yet.'},
{id:'sample-01',finish:null,status:'Load error',gates:'Malformed receipt',integrity:'Unavailable',completed:false,note:'Sample: invalid JSON. Folder remains visible; no outcome or completion time is inferred.'}
 ];
let importVersion=0,realMode=false;let runs=sampleRuns,page=0;const pageSize=20;let matchingIds=new Set(),displayedIds=new Set();
function receiptConcerns(receipt){
 const concerns=[];
 if(receipt.status==='PASS'){
  if(receipt.exit_code!==0)concerns.push('Recorded PASS has a missing or nonzero exit code');
  if(!receipt.gates?.length)concerns.push('Recorded PASS has no gate records');
  else if(receipt.gates.some(g=>g.status!=='PASS'))concerns.push('Recorded PASS includes a non-passing gate');
  if(!receipt.repositories_before||!receipt.repositories_after)concerns.push('Recorded PASS is missing repository snapshots');
  if(receipt.observed_git_state_changed!==false)concerns.push('Recorded PASS lacks an unchanged-state observation');
 }
 if(receipt.started_at&&Date.parse(receipt.started_at)>Date.parse(receipt.finished_at))concerns.push('Recorded finish precedes start');
 return concerns;
}
function importedConcerns(r){
 const b=r.bundle;if(!b)return [];
 const reasons=[];
 if(r.status!=='PASS')reasons.push('Recorded run '+r.status);
 if(r.integrity!=='PASS')reasons.push('Artifact integrity '+r.integrity);
 if(b.catalogError)reasons.push('Catalog unavailable: '+b.catalogError);
 if(b.catalog?.status!=='PASS'&&b.catalog)reasons.push('Recorded catalog '+b.catalog.status);
 if(b.receipt.observed_git_state_changed===true)reasons.push('Repository state changed during execution');
 return [...reasons,...receiptConcerns(b.receipt)];
}
function reviewReason(r){if(r.bundle)return importedConcerns(r).join(' · ')||'No recorded failure or receipt concern detected';if(r.loadError)return r.loadError;if(r.status==='Load error')return 'Receipt could not be read';if(r.status==='RUNNING')return 'Checkpoint only · process state unknown';if(r.integrity.startsWith('FAIL'))return 'Artifact mismatch · evidence unverified';if(r.status==='ERROR')return 'Repository changed during execution';if(r.status==='FAIL')return 'Catalog gate failed';return 'No recorded failure';}
function localTime(value){return value?new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value)):'Completion not recorded';}
let pair=[null,null],selected=null;const $=id=>document.getElementById(id),n=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
function motionBehavior(){return typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';}
function pill(text){const e=n('span',text);e.className='pill '+text;return e;}
function attention(r){if(r.bundle)return importedConcerns(r).length>0;return r.status!=='PASS'||r.integrity.startsWith('FAIL')||(realMode&&r.integrity!=='PASS')||!!r.bundle?.catalogError;}
function filteredRuns(){const q=$('search').value.toLowerCase(),f=$('filter').value;return runs.filter(r=>(r.id+' '+r.gates+' '+(r.bundle?.catalog?.results||[]).map(d=>d.path+' '+(d.report?.design?.name??'')).join(' ')).toLowerCase().includes(q)&&(f==='all'||f==='attention'&&attention(r)||f==='completed'&&r.completed||f==='unchecked'&&r.integrity==='Not checked'||f==='integrity_review'&&r.integrity!=='PASS'||f==='integrity_problem'&&/^(FAIL|ERROR)/.test(r.integrity)||f==='unbound'&&r.integrity==='UNBOUND'||f==='load_error'&&r.status==='Load error'||f==='catalog_unavailable'&&!!r.bundle?.catalogError||f===r.status)).sort((a,b)=>($('sort').value==='review'?(Number(attention(b))-Number(attention(a))):0)||(Date.parse(b.finish)||0)-(Date.parse(a.finish)||0));}
function render(){const visible=filteredRuns();$('count').textContent=visible.length+' of '+runs.length+(realMode?' imported runs · times in ':' sample runs · times in ')+Intl.DateTimeFormat().resolvedOptions().timeZone+' · '+($('sort').value==='review'?'review priority, then completion time':'completion times newest first; unknown times last');matchingIds=new Set(visible.map(r=>r.id));page=Math.min(page,Math.max(0,Math.ceil(visible.length/pageSize)-1));const pageRows=visible.slice(page*pageSize,(page+1)*pageSize);displayedIds=new Set(pageRows.map(r=>r.id));$('page-status').textContent=visible.length?'Rows '+(page*pageSize+1)+'–'+(page*pageSize+pageRows.length)+' of '+visible.length:'No matching rows';$('previous').disabled=page===0;$('next').disabled=(page+1)*pageSize>=visible.length;$('rows').replaceChildren();for(const r of pageRows){const tr=n('tr');tr.setAttribute('role','row');if(selected===r.id)tr.className='selected';const id=n('td',r.id);const time=n('small',localTime(r.finish));time.title=r.finish||'Unknown';id.append(time);const outcome=n('td');outcome.append(pill(r.status),n('small',r.gates),n('small',reviewReason(r)));const integrity=n('td',r.integrity);if(r.bundle){integrity.append(n('small',r.integrity==='PASS'?r.bundle.integrity.file_count+' referenced files match':(r.bundle.integrity.reasons||[]).join(' · ')));}if(r.integrity==='Not checked')integrity.append(n('small','No hash verification performed'));const actions=n('td');for(const [label,action]of [['Inspect',()=>inspect(r)],['Use as A',()=>choose(0,r)],['Use as B',()=>choose(1,r)]]){const b=n('button',label);b.style.margin='0 5px 5px 0';b.disabled=label!=='Inspect'&&!r.completed;b.onclick=action;b.setAttribute('aria-label',label+' · '+r.id);if(label==='Inspect')b.dataset.runId=r.id;if(label==='Use as A'||label==='Use as B'){const chosen=pair[label==='Use as A'?0:1]?.id===r.id;b.setAttribute('aria-pressed',String(chosen));if(chosen)b.textContent=label==='Use as A'?'Selected A':'Selected B';}actions.append(b);}if(!r.completed)actions.append(n('small',r.status==='Load error'?'Comparison unavailable: receipt could not be read.':'Comparison unavailable: completed receipt required.'));
for(const [cell,label]of [[id,'Run / recorded finish'],[outcome,'Outcome / gates'],[integrity,'Artifact integrity'],[actions,'Actions']]){cell.setAttribute('role','cell');const heading=n('span',label);heading.className='mobile-label';heading.setAttribute('aria-hidden','true');cell.prepend(heading);}
tr.append(id,outcome,integrity,actions);$('rows').append(tr);}if(!visible.length){const tr=n('tr'),td=n('td','No matching runs. Clear the search or change the filter.');td.colSpan=4;tr.append(td);$('rows').append(tr);}updateVisibility();}
function inspect(r){if(r.bundle){inspectBundle(r);return;}selected=r.id;render();const d=$('detail');d.hidden=false;d.replaceChildren(n('h2',r.id),pill(r.status),n('p',reviewReason(r)),n('p',r.note||r.loadError||'No additional details'),n('p','Recorded completion: '+(r.finish||'Not recorded')),n('p','Artifact integrity: '+r.integrity));if(r.sha){const details=n('details');details.append(n('summary','Recorded repository snapshot'),n('pre',JSON.stringify({commit:r.sha,dirty:r.dirty,source:'SAMPLE execution-time observation'},null,2)));d.append(details);}d.append(n('p','Real implementation: verify selected artifact bytes before presenting a hash result. Receipt authenticity and current repository state remain separate.'));const close=n('button','Close inspection');close.onclick=()=>{d.hidden=true;selected=null;render();const buttons=Array.from($('rows').querySelectorAll('button'));(buttons.find(b=>b.dataset.runId===r.id)||$('search')).focus();};d.prepend(close);d.scrollIntoView({block:'nearest',behavior:motionBehavior()});d.focus({preventScroll:true});}
function updateVisibility(){for(let i=0;i<2;i++){const el=$('visibility-'+i);if(el)el.textContent=pair[i]&&!matchingIds.has(pair[i].id)?'Hidden by current filters · selection retained':pair[i]&&!displayedIds.has(pair[i].id)?'On another history page · selection retained':'';}}
function revealRun(r){
  if(!matchingIds.has(r.id)){$('search').value='';$('filter').value='all';}
  const index=filteredRuns().findIndex(row=>row.id===r.id);
  page=Math.max(0,Math.floor(index/pageSize));render();
  const button=Array.from($('rows').querySelectorAll('button')).find(b=>b.dataset.runId===r.id);
  if(button){button.scrollIntoView({block:'center',behavior:motionBehavior()});button.focus({preventScroll:true});}
}
function clearFilters(){$('search').value='';$('filter').value='all';page=0;render();}
$('clear-filters').onclick=clearFilters;
$('previous').onclick=()=>{page--;render();};
$('next').onclick=()=>{page++;render();};
function choose(i,r){pair[i]=r;drawPair();render();}
function drawPair(){$('compare').textContent=realMode?'Compare recorded runs':'Show sample comparison';for(let i=0;i<2;i++){const el=$(i?'b':'a');el.replaceChildren(n('h3',i?'Comparison B':'Baseline A'));const visibility=n('small');visibility.id='visibility-'+i;el.append(visibility);const r=pair[i];el.append(n('p',r?r.id+' · recorded '+r.status:'Choose a completed run'));if(r){el.append(n('p','Recorded finish: '+localTime(r.finish)),n('p','Artifact integrity: '+r.integrity));if(r.bundle){for(const concern of receiptConcerns(r.bundle.receipt))el.append(n('p',concern));el.append(n('p','Exit: '+(r.bundle.receipt.exit_code??'Not recorded')),evidence('Recorded repository provenance',{before:r.bundle.receipt.repositories_before??null,after:r.bundle.receipt.repositories_after??null}),evidence('Integrity details',r.bundle.integrity));}const reveal=n('button','Find in history');reveal.title='Clear filters if needed and jump to this run';reveal.onclick=()=>revealRun(r);el.append(reveal);const remove=n('button','Remove '+(i?'B':'A'));remove.onclick=()=>{pair[i]=null;drawPair();render();};el.append(remove);}}$('compare').disabled=!pair.every(Boolean);$('clear').disabled=!pair.some(Boolean);const swapButton=$('swap');if(swapButton)swapButton.disabled=!pair.some(Boolean);$('selection-status').textContent=pair.every(Boolean)?(pair[0].id===pair[1].id?'Same run on both sides — useful as a no-change check.':(Date.parse(pair[0].finish)>Date.parse(pair[1].finish)?'A → B compares a newer run to an older run. Swap to reverse direction.':'A → B follows the selected direction; run times do not establish a shared code lineage.')):pair.some(Boolean)?'Choose the remaining comparison slot from the history table.':'Choose baseline A and comparison B from any completed rows.';$('comparison').replaceChildren();updateTray();}
$('compare').onclick=()=>{const [a,b]=pair;if(a.bundle&&b.bundle){compareImported(a,b);return;}const out=$('comparison');out.replaceChildren(n('h3','Sample comparison'),n('p',a.id===b.id?'Same run selected on both sides; no differences.':'Recorded outcome: '+a.status+' → '+b.status),n('p','A gates: '+a.gates),n('p','B gates: '+b.gates),n('p','This interaction does not compute real findings or verify artifacts. The implemented view will use the existing comparison engine.'));};
const swap=n('button','Swap A / B');swap.id='swap';swap.onclick=()=>{pair.reverse();drawPair();render();};$('clear').before(swap);$('clear').onclick=()=>{pair=[null,null];drawPair();render();};$('reset').onclick=()=>{importVersion++;$('cancel-import').disabled=true;$('clear-import').disabled=true;realMode=false;$('scale').disabled=false;$('mode-notice').textContent='Sample mode. Repository discovery is simulated.';$('import-status').textContent='';$('search').value='';$('filter').value='all';$('sort').value='newest';$('scale').value='6';runs=sampleRuns;page=0;renderStats();selected=null;pair=[null,null];drawPair();render();$('detail').hidden=true;$('detail').replaceChildren(n('h2','Inspect a run'),n('p','Select Inspect to see its recorded evidence.'));};const refilter=()=>{page=0;render();};$('search').oninput=refilter;$('filter').onchange=refilter;$('sort').onchange=refilter;
function renderStats(){$('stats').replaceChildren();for(const [label,value]of [[realMode?'Imported runs':'Sample runs',runs.length],['Need review',runs.filter(attention).length],['Completed',runs.filter(r=>r.completed).length],[realMode?'Integrity needs review':'Integrity not checked',runs.filter(r=>realMode?r.integrity!=='PASS':r.integrity==='Not checked').length]]){const c=n('button',label);c.className='card';c.style.textAlign='left';c.append(n('b',value));c.onclick=()=>{$('filter').value=({'Sample runs':'all','Imported runs':'all','Need review':'attention','Completed':'completed','Integrity not checked':'unchecked','Integrity needs review':'integrity_review'})[label];page=0;render();};$('stats').append(c);}}
renderStats();
const tray=n('div');tray.id='selection-tray';tray.setAttribute('aria-label','Comparison selection');document.body.append(tray);
function updateTray(){if(!document.getElementById('selection-tray'))return;tray.hidden=!pair.some(Boolean);tray.replaceChildren(n('span','A: '+(pair[0]?.id??'Choose a run')+'  /  B: '+(pair[1]?.id??'Choose a run')));const jump=n('button','Review selection');jump.onclick=()=>{$('a').parentElement.scrollIntoView({block:'center',behavior:motionBehavior()});$('compare').disabled?$('clear').focus({preventScroll:true}):$('compare').focus({preventScroll:true});};tray.append(jump);}
$('scale').onchange=()=>{page=0;runs=$('scale').value==='6'?sampleRuns:Array.from({length:100},(_,i)=>{const base=sampleRuns[i%6];return {...base,id:'sample-'+String(100-i).padStart(3,'0')+(i%9===0?'-extended-catalog-validation-history-example':''),finish:base.finish?new Date(Date.parse('2026-09-27T03:30:00Z')-i*3600000).toISOString():null};});pair=[null,null];selected=null;$('detail').hidden=true;renderStats();drawPair();render();};

const repoSamples=[
{id:'automation',name:'cad-automation',path:'/sample/dev/cad-automation',branch:'main',sha:'sample-current-automation',dirty:false},
{id:'core',name:'zcad-core',path:'/sample/dev/zcad-core',branch:null,sha:'sample-current-core',dirty:true},
{id:'restricted',name:'restricted-project',path:'/sample/dev/restricted-project',error:'Access unavailable · repository identity not established'}
];
const observationTime='2026-09-27T03:40:00Z';
let trackedRepos=new Set(),discoveryScope=null;
function renderRepos(){
 const list=$('repo-list');list.replaceChildren();
 if(!trackedRepos.size)list.append(n('p','No sample repositories added.'));
 for(const r of repoSamples.filter(r=>trackedRepos.has(r.id))){
  const card=n('div');card.className='card repo-card';
  card.append(n('h3',r.name),n('p',r.path),pill(r.dirty?'Changes observed':'Clean observed'),n('p',r.branch?'Branch: '+r.branch:'Detached HEAD · no branch checked out'),n('p','Sample observation: '+localTime(observationTime)));
  const details=n('details');details.append(n('summary','Observation evidence'),n('pre',JSON.stringify({source:'SYNTHETIC repository observation',observed_at:observationTime,sha:r.sha,dirty:r.dirty,branch:r.branch},null,2)));
  card.append(details,n('p','Historical run association: not established'));
  const remove=n('button','Remove from overview');remove.setAttribute('aria-label','Remove '+r.name+' from overview');
  remove.onclick=()=>{trackedRepos.delete(r.id);renderRepos();renderCandidates();$('repo-status').textContent=r.name+' removed from this demo overview.';};card.append(remove);list.append(card);
 }
}
function renderCandidates(){
 const root=$('repo-candidates');root.replaceChildren();
 if(discoveryScope!=='workspace')return;
 root.append(n('h3','2 repository candidates · 1 inaccessible folder'));
 for(const r of repoSamples){
  const row=n('div');row.className='repo-candidate';row.append(n('strong',r.name),n('p',r.path));
  if(r.error)row.append(n('p',r.error));
  else{const add=n('button',trackedRepos.has(r.id)?'Added to overview':'Add sample repository');add.disabled=trackedRepos.has(r.id);add.setAttribute('aria-label','Add '+r.name+' to overview');add.onclick=()=>{trackedRepos.add(r.id);renderRepos();renderCandidates();$('repo-status').textContent=r.name+' added · historical runs unchanged.';};row.append(add);}
  root.append(row);
 }
}
$('discover').onclick=()=>{discoveryScope=$('repo-scope').value;renderCandidates();$('repo-status').textContent=discoveryScope==='workspace'?'Sample discovery complete. Review candidates below.':discoveryScope==='empty'?'Sample discovery complete: no repositories found. Existing overview entries retained.':'Sample discovery unavailable: folder access denied. No results inferred; existing overview entries retained.';};
$('clear-repos').onclick=()=>{trackedRepos.clear();discoveryScope=null;$('repo-scope').value='workspace';renderRepos();renderCandidates();$('repo-status').textContent='No discovery performed.';};
const resetHistory=$('reset').onclick;$('reset').onclick=()=>{resetHistory();$('clear-repos').onclick();};
renderRepos();

function evidence(title,value){const d=n('details');d.append(n('summary',title),n('pre',typeof value==='string'?value:JSON.stringify(value,null,2)));return d;}

function designPriority(r){return r.status!=='PASS'?0:(r.report?.checks||[]).some(c=>c.status==='NOT_CHECKED')?1:2;}
function labeledCell(label,text){const td=n('td',text),hint=n('span',label);hint.className='mobile-label';hint.setAttribute('aria-hidden','true');td.prepend(hint);return td;}
function designDetails(result){
 const d=n('details'),checks=result.report?.checks||[];
 const failing=checks.filter(c=>!['PASS','NOT_CHECKED'].includes(c.status)),unchecked=checks.filter(c=>c.status==='NOT_CHECKED'),passing=checks.filter(c=>c.status==='PASS');
 d.open=designPriority(result)<2;
 d.append(n('summary',result.path+' · '+result.status+' · '+failing.length+' findings · '+unchecked.length+' unchecked'));
 if(result.error)d.append(n('p',typeof result.error==='string'?result.error:JSON.stringify(result.error)));
 d.append(n('p','Recorded coverage: '+(result.report?.coverage??'Not recorded')));
 if(result.report?.scope)d.append(n('p',result.report.scope));
 for(const [title,items]of [['Findings',failing],['Unchecked areas',unchecked]]){
  if(!items.length)continue;d.append(n('h3',title));
  for(const c of items)d.append(n('p',c.status+' · '+c.code+(c.part_name?' / '+c.part_name:'')+' · '+(c.message??'No message recorded')));
 }
 if(!checks.length)d.append(n('p','No checks recorded. No passing coverage inferred.'));
 const pass=n('details');pass.append(n('summary','Passing checks ('+passing.length+')'));
 for(const c of passing)pass.append(n('p',c.code+(c.part_name?' / '+c.part_name:'')+' · '+(c.message??'')));d.append(pass);
 const measured=checks.filter(c=>Array.isArray(c.actual_mm)||Array.isArray(c.limits_mm));
 if(measured.length){
  d.append(n('h3','Recorded dimensions (mm)'));const table=n('table'),head=n('thead'),row=n('tr');
  for(const label of ['Part / check','Axis','Actual (mm)','Limit (mm)']){const th=n('th',label);th.scope='col';row.append(th);}head.append(row);table.append(head);
  const body=n('tbody');for(const c of measured)for(const [i,axis]of ['X','Y','Z'].entries()){const tr=n('tr');tr.append(labeledCell('Part / check',(c.part_name??'Unspecified part')+' / '+c.code),labeledCell('Axis',axis),labeledCell('Actual (mm)',c.actual_mm?.[i]===undefined?'Not recorded':String(c.actual_mm[i])),labeledCell('Limit (mm)',c.limits_mm?.[i]===undefined?'Not recorded':String(c.limits_mm[i])));body.append(tr);}
  table.append(body);d.append(table);
 }
 d.append(evidence('Complete recorded design evidence',result));return d;
}
function inspectBundle(r){
 selected=r.id;render();const d=$('detail'),b=r.bundle;d.hidden=false;
 const close=n('button','Close inspection');close.onclick=()=>{d.hidden=true;selected=null;render();revealRun(r);};
 d.replaceChildren(close,n('h2',r.id),n('p','Recorded run: '+r.status+' · Artifact integrity: '+r.integrity),
 n('p','Started: '+(b.receipt.started_at??'Not recorded')+' · Finished: '+b.receipt.finished_at+' · Exit: '+(b.receipt.exit_code??'Not recorded')),
 n('p','Integrity binds artifact bytes only. Receipt authenticity, current repository state and filesystem symlink metadata are unverified. Extra files are outside the binding.'),
 evidence('Integrity result',b.integrity),evidence('Execution-time repositories before',b.receipt.repositories_before??'Not recorded'),evidence('Execution-time repositories after',b.receipt.repositories_after??'Not recorded'));
 const concerns=importedConcerns(r);
 if(concerns.length){d.append(n('h3','Needs review'));for(const reason of concerns)d.append(n('p',reason));}
 d.append(n('p','Receipt concerns are viewer observations. The recorded run status and artifact integrity result remain separate.'));
 const passing=n('details');passing.append(n('summary','Passing gates'));
 for(const g of b.receipt.gates||[])(g.status==='PASS'?passing:d).append(evidence(g.name+' · '+g.status,g));
 d.append(passing);
 if(b.catalogError)d.append(n('p','Catalog unavailable: '+b.catalogError));
 else{d.append(n('h3','Catalog findings'));for(const result of [...b.catalog.results].sort((a,b)=>designPriority(a)-designPriority(b)))d.append(designDetails(result));d.append(evidence('Recorded catalog policy',b.catalog.policy??'Not recorded'));}
 d.append(evidence('Original receipt JSON',b.raw));d.scrollIntoView({block:'nearest',behavior:motionBehavior()});d.focus({preventScroll:true});
}
function changeTable(title,rows,label){
 const section=n('section');section.append(n('h3',title));
 if(!rows.length){section.append(n('p','No changes in recorded evidence.'));return section;}
 const table=n('table'),head=n('thead'),h=n('tr');
 for(const text of ['Identity','Change','A','B']){const th=n('th',text);th.scope='col';h.append(th);}head.append(h);table.append(head);
 const body=n('tbody');
 for(const row of rows){const tr=n('tr');for(const [heading,text]of [['Identity',row.key],['Change',row.kind],['A',row.before.length?row.before.map(label).join(' | '):'Not present'],['B',row.after.length?row.after.map(label).join(' | '):'Not present']]){const cell=n('td',text),caption=n('span',heading);caption.className='mobile-label';cell.prepend(caption);tr.append(cell);}body.append(tr);}
 table.append(body);section.append(table);return section;
}
function compareImported(a,b){
 const out=$('comparison'),diff=ZcadCompare.compareRuns(a.bundle,b.bundle);
 out.replaceChildren(n('h3','Recorded evidence · A → B'));
 if(a.integrity!=='PASS'||b.integrity!=='PASS')out.append(n('p','One or both runs have unverified or unbound artifacts.'));
 out.append(n('p','Exact gate names and design paths are compared. Removed findings do not establish a fix; duplicate identities remain ambiguous.'));
 out.append(changeTable('Gate changes',diff.gates.filter(g=>g.kind!=='Unchanged'),g=>g.status));
for(const g of diff.gates.filter(g=>g.kind!=='Unchanged'))out.append(evidence(g.key+' · '+g.kind,g));
 if(diff.policyChanged)out.append(n('p','Catalog policies differ.'));
 if(diff.designs===null)out.append(n('p','Design comparison unavailable: both valid catalogs are required.'));
 else {out.append(changeTable('Design changes',diff.designs.filter(r=>r.kind!=='Unchanged'),r=>r.status));}
if(diff.designs)for(const r of diff.designs.filter(r=>r.kind!=='Unchanged')){
 const design=n('details');design.append(n('summary',r.key+' · '+r.kind));
 if(r.before.length>1||r.after.length>1)design.append(n('p','Ambiguous design identity: check pairing is unavailable.'));
 else{
  const findings=ZcadCompare.findings(r.before[0],r.after[0]);
  const changed=findings.filter(f=>f.kind!=='Unchanged');
  design.append(changeTable('Changed checks',changed,c=>c.status+(c.message?' · '+c.message:'')));
  if(!changed.length)design.append(n('p','No check-record changes. Inspect complete evidence for changed dimensions, coverage, or other design fields.'));
  if(changed.some(f=>f.kind==='Removed'))design.append(n('p','Removed checks are absent from B; this does not establish resolution.'));
  for(const f of changed)design.append(evidence('Check evidence · '+f.key,f));
  const same=n('details');same.append(n('summary',findings.filter(f=>f.kind==='Unchanged').length+' unchanged check records'),changeTable('Unchanged checks',findings.filter(f=>f.kind==='Unchanged'),c=>c.status));design.append(same);
 }
 design.append(evidence('Complete A/B design evidence',{baseline:r.before,comparison:r.after}));out.append(design);
}
 out.append(n('p',diff.gates.filter(g=>g.kind!=='Unchanged').length+' changed gate records · '+(diff.designs?.filter(r=>r.kind!=='Unchanged').length??'Unavailable')+' changed design records'));
}
$('cancel-import').onclick=()=>{
 importVersion++;$('cancel-import').disabled=true;$('reports').value='';
 $('import-status').textContent='Import canceled · '+runs.length+' fully processed folders retained. Remaining folders were not assessed.';
};
$('clear-import').onclick=()=>{
 importVersion++;runs=[];pair=[null,null];selected=null;page=0;realMode=true;
 $('detail').hidden=true;$('detail').replaceChildren();$('reports').value='';$('cancel-import').disabled=true;$('clear-import').disabled=true;$('scale').disabled=true;
 $('mode-notice').textContent='No imported evidence loaded. Choose a reports folder, or Reset demo to explore sample data.';
 $('import-status').textContent='Imported evidence cleared from this page. Original files were not changed.';
 renderStats();drawPair();render();
};
$('reports').onchange=async()=>{
 const files=Array.from($('reports').files);if(!files.length)return;
 const version=++importVersion;$('cancel-import').disabled=false;$('clear-import').disabled=false;$('search').value='';$('filter').value='all';realMode=true;runs=[];pair=[null,null];selected=null;page=0;$('detail').hidden=true;$('scale').disabled=true;
 $('mode-notice').textContent='Imported evidence · files stay in this tab. Integrity is independent of gate success. Repository discovery below remains simulated.';
 renderStats();drawPair();render();
 const groups=new Map();
 for(const f of files){const prefix=f.webkitRelativePath.slice(0,-f.name.length);if(!groups.has(prefix))groups.set(prefix,[]);groups.get(prefix).push(f);}
 const candidates=[...groups].filter(([,fs])=>fs.some(f=>f.name==='receipt.json'));
 const digest=async bytes=>{if(!globalThis.crypto?.subtle)throw Error('SHA-256 unavailable');return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');};
 for(const [prefix,fs]of candidates){
  if(version!==importVersion)return;$('import-status').textContent='Reading and verifying '+(runs.length+1)+' of '+candidates.length+' run folders…';
  let row;try{const bundle=await ZcadCompare.readBundle(fs,validateReceipt,ZcadModel.validate,verifyIntegrity,digest);
   row={id:prefix.replace(/\/$/,''),finish:bundle.receipt.finished_at,status:bundle.receipt.status,gates:(bundle.receipt.gates||[]).map(g=>g.name+' '+g.status).join(' · '),integrity:bundle.integrity.status,completed:true,bundle};
  }catch(e){row={id:prefix,finish:null,status:'Load error',gates:'Receipt not accepted as completed',integrity:'Unavailable',completed:false,loadError:e.message};}
  if(version!==importVersion)return;runs.push(row);renderStats();render();
 }
 if(version!==importVersion)return;
 $('import-status').textContent=candidates.length?runs.length+' run folders read · '+runs.filter(r=>r.completed).length+' completed receipts · '+runs.filter(r=>r.integrity==='PASS').length+' integrity PASS · '+runs.filter(r=>r.loadError).length+' rejected or incomplete.':'No receipt.json found in selected files.';
 $('reports').value='';$('cancel-import').disabled=true;
};
drawPair();render();

let inventoryVersion=0,inventorySnapshot=null,inventoryPage=0;
function renderInventory(){
 const out=$('inventory-table');out.replaceChildren();
 if(!inventorySnapshot)return;
 const query=$('inventory-search').value.trim().toLowerCase(),filter=$('inventory-filter').value;
 const rows=inventorySnapshot.repositories.filter(r=>(r.path+' '+(r.branch??'')+' '+(r.head??'')).toLowerCase().includes(query)&&(!filter||filter==='all'||filter==='error'&&r.status==='ERROR'||filter==='changed'&&r.status==='OBSERVED'&&r.dirty||filter==='clean'&&r.status==='OBSERVED'&&!r.dirty||filter==='detached'&&r.status==='OBSERVED'&&r.branch===null));
 inventoryPage=Math.min(inventoryPage,Math.max(0,Math.ceil(rows.length/20)-1));
 $('inventory-page').textContent=rows.length?'Rows '+(inventoryPage*20+1)+'–'+Math.min(rows.length,(inventoryPage+1)*20)+' of '+rows.length+' matching · '+inventorySnapshot.repositories.length+' total':'No matching repositories';
 $('inventory-prev').disabled=inventoryPage===0;
 $('inventory-next').disabled=(inventoryPage+1)*20>=rows.length;
 const table=n('table');table.setAttribute('aria-label','Imported repository observations');
 const head=n('thead'),headers=n('tr');
 for(const label of ['Repository','Observed state','Branch','Details']){const th=n('th',label);th.scope='col';headers.append(th);}head.append(headers);table.append(head);
 const body=n('tbody');
 for(const r of rows.slice(inventoryPage*20,(inventoryPage+1)*20)){
  const row=n('tr'),name=labeledCell('Repository',r.path.split('/').filter(Boolean).pop()||r.path);name.title=r.path;
  const state=labeledCell('Observed state',r.status==='ERROR'?'Observation error':r.dirty?'Changes observed':'Clean observed');
  const branch=labeledCell('Branch',r.status==='ERROR'?'Unavailable':r.branch??'Detached HEAD');
  const details=labeledCell('Details','');details.append(evidence('Observation',r));
  row.append(name,state,branch,details);body.append(row);
 }
 if(!rows.length){const row=n('tr'),cell=n('td','No matching repositories. Clear the search or change the filter.');cell.colSpan=4;row.append(cell);body.append(row);}
 table.append(body);out.append(table);
}
for(const id of ['inventory-search','inventory-filter'])$(id)[id==='inventory-search'?'oninput':'onchange']=()=>{inventoryPage=0;renderInventory();};
$('inventory-prev').onclick=()=>{inventoryPage--;renderInventory();};
$('inventory-next').onclick=()=>{inventoryPage++;renderInventory();};
$('inventory-clear-filters').onclick=()=>{$('inventory-search').value='';$('inventory-filter').value='all';inventoryPage=0;renderInventory();};
$('clear-inventory').onclick=()=>{
 inventoryVersion++;$('inventory').value='';$('inventory-results').replaceChildren();
 inventorySnapshot=null;inventoryPage=0;$('inventory-controls').hidden=true;$('inventory-table').replaceChildren();
 $('inventory-status').textContent='No repository snapshot loaded.';
};
$('inventory').onchange=async()=>{
 const file=$('inventory').files?.[0];if(!file)return;
 const version=++inventoryVersion;
 $('inventory-status').textContent='Reading repository snapshot…';
 try{
  if(file.size>5*1024*1024)throw Error('Snapshot exceeds 5 MiB');
  const raw=await file.text();
  const snapshot=ZcadRepositories.validateInventory(JSON.parse(raw));
  if(version!==inventoryVersion)return;
  const out=$('inventory-results');out.replaceChildren();
  out.append(n('p','Snapshot: '+localTime(snapshot.finished_at)+' · '+snapshot.root));
  out.append(evidence('Scan scope and timing',{root:snapshot.root,started_at:snapshot.started_at,finished_at:snapshot.finished_at,max_depth:snapshot.max_depth,coverage:'Stops at repository roots. Nested repositories and bare repositories excluded.'}));
  if(snapshot.issues.length)out.append(evidence(snapshot.issues.length+' scan issues',snapshot.issues));
  out.append(evidence('Original inventory JSON',raw));
  inventorySnapshot=snapshot;inventoryPage=0;$('inventory-search').value='';$('inventory-filter').value='all';$('inventory-controls').hidden=false;renderInventory();
  $('inventory-status').textContent=snapshot.repositories.length+' repository records · '+snapshot.repositories.filter(r=>r.status==='ERROR').length+' observation errors · '+snapshot.issues.length+' scan issues. Imported snapshot; live state and authenticity unverified.';
 }catch(e){if(version!==inventoryVersion)return;$('inventory-status').textContent='Import rejected: '+e.message+'. Previous snapshot retained.';}
 if(version===inventoryVersion)$('inventory').value='';
};
