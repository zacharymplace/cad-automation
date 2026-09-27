(function(root){
  'use strict';
  const statuses=['PASS','FAIL','ERROR'];
  function validate(d){
    if(!d || d.schema_version!=='1.0' || !statuses.includes(d.status) || !Array.isArray(d.results)) throw Error('Expected a ZCAD schema 1.0 catalog report with status and results.');
    if(d.design_count!==d.results.length || !d.counts) throw Error('Design count is missing or inconsistent.');
    const counts={PASS:0,FAIL:0,ERROR:0}, paths=new Set();
    for(const r of d.results){
      if(!r || typeof r.path!=='string' || !r.path || paths.has(r.path) || !statuses.includes(r.status)) throw Error('Invalid or duplicate design result.');
      paths.add(r.path);counts[r.status]++;
      if(r.status!=='ERROR' && (!r.report || !Array.isArray(r.report.checks))) throw Error('Design report is missing checks.');
      if(r.report){
        if(!Array.isArray(r.report.checks)) throw Error('Invalid checks.');
        for(const c of r.report.checks) if(!c || typeof c.code!=='string' || !['PASS','FAIL','ERROR','WARN','WARNING','NOT_CHECKED'].includes(c.status)) throw Error('Unsupported check status or code.');
      }
    }
    for(const k of statuses) if(counts[k]!==d.counts[k]) throw Error('Reported counts do not match design results.');
    if(d.status==='PASS' && (counts.FAIL || counts.ERROR || !d.results.length)) throw Error('PASS conflicts with reported results.');
    return d;
  }
  function failed(r){return ['FAIL','ERROR'].includes(r.status);}
  function unchecked(r){return (r.report?.checks??[]).some(c=>c.status==='NOT_CHECKED');}
  function priority(r){return failed(r)?0:unchecked(r)?1:2;}
  function visibleResults(results,query='',filter=''){
    return results.filter(r=>(filter==='failed'?failed(r):filter==='unchecked'?unchecked(r):!filter||r.status===filter)
      && (r.path+' '+(r.report?.design?.name??'')).toLowerCase().includes(query.toLowerCase()))
      .sort((a,b)=>priority(a)-priority(b));
  }
  function selectResult(rows,current){return rows.some(r=>r.path===current)?current:rows[0]?.path;}
  root.ZcadModel={validate,visibleResults,selectResult};
  if(typeof module!=='undefined') module.exports=root.ZcadModel;
})(globalThis);
