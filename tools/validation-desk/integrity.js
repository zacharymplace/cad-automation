// Matches zcad.run_integrity artifact_integrity schema 1.0.
async function verifyIntegrity(receipt, files, digest) {
  const binding=receipt.artifact_integrity;
  if(binding==null)return {status:'UNBOUND',reasons:['Receipt has no artifact hashes']};
  try {
    if(!['PASS','FAIL','ERROR','INTERRUPTED'].includes(receipt.status))throw Error('Receipt is not finalized');
    if(binding.schema_version!=='1.0'||binding.algorithm!=='sha256')throw Error('Unsupported artifact integrity schema');
    const names=[];
    for(const gate of receipt.gates||[])for(const stream of ['stdout','stderr']){
      const name=gate[stream];
      if(typeof name!=='string'||!name||['.','..','receipt.json','receipt.tmp'].includes(name)||/[\\/]/.test(name))throw Error('Invalid artifact filename');
      names.push(name);
    }
    if(!names.length||new Set(names).size!==names.length)throw Error('Expected nonempty, unique gate artifact names');
    names.sort();
    if(!binding.files||Array.isArray(binding.files)||typeof binding.files!=='object'||JSON.stringify(Object.keys(binding.files).sort())!==JSON.stringify(names))throw Error('Hash inventory does not match gate artifact references');
    for(const name of names){
      const e=binding.files[name];
      if(!e||JSON.stringify(Object.keys(e).sort())!==JSON.stringify(['sha256','size_bytes'])||!Number.isSafeInteger(e.size_bytes)||e.size_bytes<0||typeof e.sha256!=='string'||!/^[0-9a-f]{64}$/.test(e.sha256))throw Error('Malformed hash record: '+name);
    }
    const reasons=[];
    for(const name of names){
      const f=files.get(name),e=binding.files[name];
      if(!f){reasons.push('Missing artifact: '+name);continue;}
      if(f.size!==e.size_bytes){reasons.push('Changed artifact: '+name+' (size mismatch)');continue;}
      if(f.size>10*1024*1024)throw Error('Verification limit exceeded: '+name+' (10 MiB)');
      const bytes=await f.arrayBuffer();
      if(bytes.byteLength!==e.size_bytes||await digest(bytes)!==e.sha256)reasons.push('Changed artifact: '+name+' (SHA-256 mismatch)');
    }
    return {status:reasons.length?'FAIL':'PASS',file_count:names.length,reasons};
  }catch(e){return {status:'ERROR',reasons:[e.message]};}
}
if(typeof module!=='undefined')module.exports={verifyIntegrity};
