const {test}=require('node:test');
const assert=require('node:assert/strict');
const {ZcadRepositories:{validateInventory}}=require('./repositories.js');
const fixture=()=>({schema_version:'zcad-repository-inventory/1',root:'/dev',started_at:'2026-09-27T00:00:00Z',finished_at:'2026-09-27T00:01:00Z',max_depth:2,visited_directories:2,issues:[],repositories:[{path:'/dev/repo',status:'OBSERVED',started_at:'2026-09-27T00:00:00Z',observed_at:'2026-09-27T00:01:00Z',head:'a'.repeat(40),branch:null,dirty:false}]});
test('inventory retains observed evidence and accepts explicit errors',()=>{
 const x=fixture(),raw=JSON.stringify(x);assert.equal(validateInventory(x),x);assert.equal(JSON.stringify(x),raw);
 x.repositories[0]={...x.repositories[0],status:'ERROR',error:'Unavailable'};validateInventory(x);
});
test('inventory rejects ambiguous paths, unknown states and malformed observations',()=>{
 for(const mutate of [x=>x.repositories.push(x.repositories[0]),x=>x.repositories[0].dirty='false',x=>x.repositories[0].head='short',x=>x.repositories[0].status='PASS',x=>x.finished_at='bad',x=>x.schema_version='2']){
  const x=fixture();mutate(x);assert.throws(()=>validateInventory(x));
 }
});
