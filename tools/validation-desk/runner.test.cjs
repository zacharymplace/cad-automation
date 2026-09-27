const {test}=require('node:test');
const assert=require('node:assert/strict');
const {validateReceipt}=require('./runner.js');
test('preserves checkpoint and execution provenance without rewriting',()=>{
 const r={schema_version:'1.0',status:'RUNNING',started_at:'2026-09-26T23:00:00+00:00',repositories_before:{core:{commit:'abc',dirty:true,status_porcelain:' M source.py'}},gates:[{name:'tests',command:['python','-m','pytest'],status:'RUNNING'}]};
 const before=JSON.stringify(r);assert.equal(validateReceipt(r),r);assert.equal(JSON.stringify(r),before);
});
test('accepts setup error without gates or snapshots',()=>assert.equal(validateReceipt({schema_version:'1.0',status:'ERROR'}).status,'ERROR'));
test('rejects malformed snapshots and unknown gate status',()=>{
 assert.throws(()=>validateReceipt({schema_version:'1.0',status:'PASS',repositories_before:{core:{commit:'abc',dirty:'false'}}}));
 assert.throws(()=>validateReceipt({schema_version:'1.0',status:'PASS',gates:[{name:'tests',command:[],status:'OK'}]}));
});
