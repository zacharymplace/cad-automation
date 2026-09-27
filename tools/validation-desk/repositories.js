(function(root){
  function validateInventory(value){
    const fail=()=>{throw Error('Invalid repository inventory');};
    const text=x=>typeof x==='string'&&x.length>0;
    const date=x=>text(x)&&Number.isFinite(Date.parse(x));
    if(!value||value.schema_version!=='zcad-repository-inventory/1'||!text(value.root)||!date(value.started_at)||!date(value.finished_at)||Date.parse(value.started_at)>Date.parse(value.finished_at)||!Number.isInteger(value.max_depth)||value.max_depth<0||value.max_depth>6||!Number.isInteger(value.visited_directories)||value.visited_directories<0||!Array.isArray(value.repositories)||!Array.isArray(value.issues))fail();
    const paths=new Set();
    for(const r of value.repositories){
      if(!r||!text(r.path)||paths.has(r.path)||!date(r.started_at)||!date(r.observed_at)||Date.parse(r.started_at)>Date.parse(r.observed_at))fail();
      paths.add(r.path);
      if(r.status==='OBSERVED'){
        if(!/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(r.head)||typeof r.dirty!=='boolean'||!(r.branch===null||text(r.branch)))fail();
      }else if(r.status!=='ERROR'||!text(r.error))fail();
    }
    for(const issue of value.issues)if(!issue||!text(issue.path)||!text(issue.reason))fail();
    return value;
  }
  root.ZcadRepositories={validateInventory};
})(typeof module==='object'?module.exports:globalThis);
