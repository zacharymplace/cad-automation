const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {verifyIntegrity}=require('./integrity.js');
const digest=async b=>createHash('sha256').update(Buffer.from(b)).digest('hex');
function fixture(){
 const files=new Map([['test.stdout.log',new Blob(['first\n'])],['test.stderr.log',new Blob([])]]);
 const r={status:'FAIL',gates:[{stdout:'test.stdout.log',stderr:'test.stderr.log'}],artifact_integrity:{schema_version:'1.0',algorithm:'sha256',files:{'test.stdout.log':{sha256:createHash('sha256').update('first\n').digest('hex'),size_bytes:6},'test.stderr.log':{sha256:createHash('sha256').update('').digest('hex'),size_bytes:0}}}};
 return {r,files};
}
test('failed run can have matching bytes; receipt unchanged',async()=>{const {r,files}=fixture();const raw=JSON.stringify(r);assert.equal((await verifyIntegrity(r,files,digest)).status,'PASS');assert.equal(JSON.stringify(r),raw);});
for(const change of ['same-size','missing','mixed'])test('detect '+change,async()=>{const {r,files}=fixture();if(change==='missing')files.delete('test.stdout.log');else files.set('test.stdout.log',new Blob([change==='same-size'?'other\n':'another run']));assert.equal((await verifyIntegrity(r,files,digest)).status,'FAIL');});
for(const change of ['traversal','inventory','boolean-size','running','algorithm','duplicate'])test('reject '+change,async()=>{const {r,files}=fixture();if(change==='traversal')r.gates[0].stdout='../outside';if(change==='inventory')delete r.artifact_integrity.files['test.stderr.log'];if(change==='boolean-size')r.artifact_integrity.files['test.stderr.log'].size_bytes=false;if(change==='running')r.status='RUNNING';if(change==='algorithm')r.artifact_integrity.algorithm='md5';if(change==='duplicate')r.gates[0].stderr=r.gates[0].stdout;assert.equal((await verifyIntegrity(r,files,digest)).status,'ERROR');});
test('legacy receipts remain unbound',async()=>assert.equal((await verifyIntegrity({status:'PASS'},new Map(),digest)).status,'UNBOUND'));
test('extra files do not change binding',async()=>{const {r,files}=fixture();files.set('extra',new Blob(['extra']));assert.equal((await verifyIntegrity(r,files,digest)).status,'PASS');});
test('crypto failure never reports pass',async()=>{const {r,files}=fixture();assert.equal((await verifyIntegrity(r,files,()=>{throw Error('unavailable');})).status,'ERROR');});
