const test=require('node:test');
const assert=require('node:assert/strict');
const {visibleResults,selectResult}=require('./model.js');
const rows=[
  {path:'passed',status:'PASS',report:{checks:[]}},
  {path:'partial',status:'PASS',report:{checks:[{status:'NOT_CHECKED'}]}},
  {path:'failed',status:'FAIL',report:{design:{name:'Bracket'},checks:[{status:'NOT_CHECKED'}]}},
  {path:'error',status:'ERROR'}
];
test('initial selection prioritizes failure, retaining receipt order among failures',()=>{
  const before=JSON.stringify(rows);
  assert.deepEqual(visibleResults(rows).map(r=>r.path),['failed','error','partial','passed']);
  assert.equal(selectResult(visibleResults(rows)),'failed');
  assert.equal(JSON.stringify(rows),before);
});
test('failed includes errors; unchecked uses recorded checks and may overlap',()=>{
  assert.deepEqual(visibleResults(rows,'','failed').map(r=>r.path),['failed','error']);
  assert.deepEqual(visibleResults(rows,'','unchecked').map(r=>r.path),['failed','partial']);
  assert.deepEqual(visibleResults(rows,'BRACKET','unchecked').map(r=>r.path),['failed']);
  assert.deepEqual(visibleResults(rows,'','PASS').map(r=>r.path),['partial','passed']);
});
test('selection survives filtering when visible and clears for empty results',()=>{
  assert.equal(selectResult(visibleResults(rows),'partial'),'partial');
  assert.equal(selectResult(visibleResults(rows,'','failed'),'partial'),'failed');
  assert.equal(selectResult(visibleResults(rows,'absent'),'failed'),undefined);
  assert.equal(selectResult(visibleResults([])),undefined);
});
test('passing catalogs with no unchecked entries still select a design',()=>{
  assert.equal(selectResult(visibleResults([rows[0]])),'passed');
});
