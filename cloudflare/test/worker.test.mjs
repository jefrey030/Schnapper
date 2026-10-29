import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import worker,{runSlot,verifyGate,MODEL,ROLES,utcSlot,TASKS,chooseApprovedTask} from '../src/worker.mjs';
import {readFileSync} from 'node:fs';
if(!globalThis.crypto) globalThis.crypto=webcrypto;
function fakeDB(){
 const slots=new Set(),reports=[],statuses=[],audit=[],control={paused:0,readFails:false,reads:0};
 return {
  slots,reports,statuses,audit,control,
  prepare(sql) {
   if(sql.startsWith('SELECT paused FROM schnapper_control')) {
    return {async first(){
     control.reads++;
     if(control.readFails) throw Error('D1 control unavailable');
     return {paused:control.paused};
    }};
   }
   return { bind(...args) {
    return { async run() {
     if(sql.startsWith('INSERT OR IGNORE')) {
      const already=slots.has(args[0]); if(!already) slots.add(args[0]);
      return {meta:{changes:already?0:1}};
     }
     if(sql.startsWith('INSERT INTO schnapper_reports')) {
      reports.push(args);return {meta:{changes:1}};
     }
     if(sql.startsWith('UPDATE schnapper_runs SET attempted_calls=')) {
      audit.push(args);return {meta:{changes:1}};
     }
     if(sql.startsWith('UPDATE schnapper_runs SET status=')) {
      statuses.push(args);return {meta:{changes:1}};
     }
     throw Error('Unexpected SQL '+sql);
    }};
   }};
  }
 };
}
function fakeEnv(overrides={}){const db=fakeDB();let calls=0;const env={RUN_ENABLED:'true',ACCOUNT_FREE_PLAN_CONFIRMED:'yes',COST_POLICY:'free-only',DB:db,
 AI:{run:async(model,req)=>{calls++;assert.equal(model,MODEL);assert.ok(req.max_tokens<=160);return {response:'Eine sachliche Antwort '+calls};}},...overrides};return {env,db,getCalls:()=>calls};}
// Mock-Auftrag ausschließlich in den Unit-Tests. scheduled() verwendet
// weiterhin die aus team/tasks.json kontrollierte (aktuell leere) Liste.
const TEST_TASKS = Object.freeze([{
 id:'S-900',goal:'Nur Testdaten prüfen',status:'open',approved:true,
 revision:1,owner:'offline-unit-test'
}]);
const runMockSlot=(env,timestamp)=>runSlot(env,timestamp,TEST_TASKS);

test('Cloudflare task snapshot exactly mirrors approved open team/tasks.json',()=>{
 const registry=JSON.parse(readFileSync(new URL('../../team/tasks.json',import.meta.url),'utf8'));
 assert.ok(Array.isArray(registry.tasks));
 const allowed=registry.tasks.filter(t=>t.status==='open'&&t.approved===true)
  .map(t=>({id:t.id,goal:t.goal,status:t.status,approved:t.approved,
             revision:t.revision,owner:t.owner}))
  .sort((a,b)=>a.id.localeCompare(b.id));
 assert.deepEqual(TASKS,allowed);
});

test('No approved open task means zero model calls and no D1 claim',async()=>{
 const x=fakeEnv();
 const out=await runSlot(x.env,Date.UTC(2026,9,22,23));
 assert.equal(out.status,'KEINE AUFGABE');
 assert.equal(out.attempted_calls,0);
 assert.equal(x.getCalls(),0);
 assert.equal(x.db.slots.size,0);
 assert.equal(x.db.audit.length,0);
});

test('Unapproved, review and proposed tasks never enable the model',async()=>{
 const invalid=[
  [{id:'S-100',goal:'Test',status:'review',approved:true,revision:1,owner:'tester'}],
  [{id:'S-100',goal:'Test',status:'open',approved:false,revision:1,owner:'tester'}],
  [{id:'S-100',goal:'Test',status:'proposed',approved:true,revision:1,owner:'tester'}],
  [{id:'S-100',goal:'Test',status:'open',approved:'true',revision:1,owner:'tester'}],
 ];
 for(let i=0;i<invalid.length;i++){
  const x=fakeEnv();
  const out=await runSlot(x.env,Date.UTC(2026,9,23,i),invalid[i]);
  assert.equal(out.status,'KEINE AUFGABE');
  assert.equal(x.getCalls(),0);
  assert.equal(x.db.slots.size,0);
 }
});

test('Incomplete approval and duplicate task IDs fail closed',async()=>{
 const missing=[
  [{id:'S-100',goal:'Test',status:'open',approved:true,revision:0,owner:'tester'}],
  [{id:'S-100',goal:'Test',status:'open',approved:true,revision:1,owner:''}],
  [TEST_TASKS[0],TEST_TASKS[0]]
 ];
 for(let i=0;i<missing.length;i++){
  const x=fakeEnv();
  const out=await runSlot(x.env,Date.UTC(2026,9,24,i),missing[i]);
  assert.equal(out.status,'KEINE AUFGABE');
  assert.equal(x.getCalls(),0);
 }
});

test('Approved task selection is deterministic and independent of array order',()=>{
 const a={id:'S-102',goal:'B',status:'open',approved:true,revision:1,owner:'tester'};
 const b={id:'S-101',goal:'A',status:'open',approved:true,revision:1,owner:'tester'};
 assert.equal(chooseApprovedTask([a,b],0).id,'S-101');
 assert.equal(chooseApprovedTask([b,a],0).id,'S-101');
 assert.equal(chooseApprovedTask([a,b],1).id,'S-102');
});

test('Fail-closed when Free tier unverified',async()=>{const x=fakeEnv({ACCOUNT_FREE_PLAN_CONFIRMED:'no'});assert.equal(verifyGate(x.env),false);assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Disabled switch prohibits inference',async()=>{const x=fakeEnv({RUN_ENABLED:'false'});assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Wrong policy prohibits inference',async()=>{const x=fakeEnv({COST_POLICY:'paid'});assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Valid slot four real invocations (mocked), four hashes and audit',async()=>{const x=fakeEnv();const t=Date.UTC(2026,9,22,4,17);const o=await runMockSlot(x.env,t);assert.equal(o.status,'ABGESCHLOSSEN');assert.equal(o.attempted_calls,4);assert.deepEqual(o.roles.map(r=>r.role),ROLES);assert.equal(x.db.reports.length,4);assert.equal(x.db.audit.length,4);assert.equal(x.db.statuses[0][0],'completed');assert.equal(x.db.reports[0][4].length,64);assert.equal((await runMockSlot(x.env,t+1000)).status,'BEREITS_VERSUCHT');assert.equal(x.getCalls(),4);});
test('Capacity failure records interrupted role and refuses retry',async()=>{const x=fakeEnv();let calls=0;x.env.AI.run=async()=>{calls++;if(calls===2)throw Error('Free quota exhausted');return {response:'eins'};};const t=Date.UTC(2026,9,22,7);const out=await runMockSlot(x.env,t);assert.equal(out.status,'BLOCKIERT');assert.equal(out.attempted_calls,2);assert.deepEqual(out.completed_roles,['LEAD']);assert.equal(x.db.statuses.at(-1)[0],'blocked');assert.equal((await runMockSlot(x.env,t)).status,'BEREITS_VERSUCHT');assert.equal(calls,2);});
test('Bad AI response blocks without fabricated report',async()=>{const x=fakeEnv();x.env.AI.run=async()=>({response:''});assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,10))).status,'BLOCKIERT');assert.equal(x.db.reports.length,0);});
test('No database or schema means zero calls',async()=>{const x=fakeEnv({DB:{prepare(){throw Error('no schema');}}});assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,3))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('DB audit failure before inference prevents charges',async()=>{const x=fakeEnv();const original=x.env.DB.prepare;x.env.DB.prepare=(sql)=>{if(sql.startsWith('UPDATE schnapper_runs SET attempted_calls='))throw Error('D1 down');return original(sql);};assert.equal((await runMockSlot(x.env,Date.UTC(2026,9,22,3))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Persistent emergency stop blocks all model calls',async()=>{
 const x=fakeEnv();x.db.control.paused=1;
 const out=await runMockSlot(x.env,Date.UTC(2026,9,22,13));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,0);
 assert.equal(x.getCalls(),0);
 assert.equal(x.db.slots.size,0);
});
test('D1 emergency stop read error fails closed',async()=>{
 const x=fakeEnv();x.db.control.readFails=true;
 const out=await runMockSlot(x.env,Date.UTC(2026,9,22,14));
 assert.equal(out.status,'BLOCKIERT');assert.equal(x.getCalls(),0);
});
test('Emergency stop in the middle of a run blocks all next calls',async()=>{
 const x=fakeEnv();let calls=0;
 x.env.AI.run=async()=>{
  calls++;
  if(calls===1)x.db.control.paused=1;
  return {response:'Abgeschlossene Antwort'};
 };
 const out=await runMockSlot(x.env,Date.UTC(2026,9,22,15));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,1);
 assert.deepEqual(out.completed_roles,['LEAD']);
 assert.equal(calls,1);
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
});
test('Malformed timestamps not accepted',async()=>{const x=fakeEnv();assert.equal((await runMockSlot(x.env,'not-a-date')).status,'BLOCKIERT');assert.equal(x.getCalls(),0);assert.equal(utcSlot(Date.UTC(2026,9,22,4,17)),'2026102204');});
test('HTTP does not expose private reports',async()=>{assert.equal((await worker.fetch()).status,404);});

test('Model reply containing a synthetic credential is rejected before D1 report',async()=>{
 const x=fakeEnv();
 const fakeToken='ghp_'+'A'.repeat(25);
 x.env.AI.run=async()=>({response:'Text '+fakeToken});
 const out=await runMockSlot(x.env,Date.UTC(2026,9,22,16));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,1);
 assert.equal(x.db.reports.length,0);
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
 assert.ok(!JSON.stringify(x.db.statuses).includes(fakeToken));
 assert.ok(!JSON.stringify(out).includes(fakeToken));
});

test('Synthetic provider credential never leaks to returned reason, D1 or console',async()=>{
 const x=fakeEnv();
 const fakeToken='github_pat_'+'A'.repeat(25);
 x.env.AI.run=async()=>{throw Error('Provider exception '+fakeToken)};
 const oldError=console.error;
 const consoleLines=[];
 console.error=(...args)=>consoleLines.push(args.join(' '));
 let out;
 try {out=await runMockSlot(x.env,Date.UTC(2026,9,22,17))}
 finally {console.error=oldError}
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,1);
 assert.ok(!JSON.stringify(out).includes(fakeToken));
 assert.ok(!JSON.stringify(x.db.statuses).includes(fakeToken));
 assert.ok(!consoleLines.join(' ').includes(fakeToken));
 assert.ok(out.reason.includes('[REDACTED]'));
 assert.ok(x.db.statuses.at(-1)[1].includes('[REDACTED]'));
});

test('Second model reply with synthetic secret stops before persisting second answer',async()=>{
 const x=fakeEnv();
 const fakeToken='sk-ant-'+'B'.repeat(20);
 let calls=0;
 x.env.AI.run=async()=>{
   calls++;
   return {response:calls===2?'Fehler '+fakeToken:'Sauberer LEAD-Plan'};
 };
 const out=await runMockSlot(x.env,Date.UTC(2026,9,22,18));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,2);
 assert.deepEqual(out.completed_roles,['LEAD']);
 assert.equal(x.db.reports.length,1);
 assert.ok(!JSON.stringify(x.db.reports).includes(fakeToken));
});

test('D1 successful HTTP result with zero changed audit rows blocks BEFORE inference',async()=>{
 const x=fakeEnv();const original=x.env.DB.prepare.bind(x.env.DB);
 x.env.DB.prepare=(sql)=>sql.startsWith('UPDATE schnapper_runs SET attempted_calls=')
  ? {bind(){return {async run(){return {meta:{changes:0}}}}}}
  : original(sql);
 const out=await runSlot(x.env,Date.UTC(2026,9,22,19));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,0);
 assert.equal(x.getCalls(),0);
 assert.equal(x.db.audit.length,0);
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
});

test('D1 unconfirmed audit metadata also prevents any model call',async()=>{
 const x=fakeEnv();const original=x.env.DB.prepare.bind(x.env.DB);
 x.env.DB.prepare=(sql)=>sql.startsWith('UPDATE schnapper_runs SET attempted_calls=')
  ? {bind(){return {async run(){return {}}}}}
  : original(sql);
 const out=await runSlot(x.env,Date.UTC(2026,9,22,20));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,0);
 assert.equal(x.getCalls(),0);
});

test('D1 no-op model report insert prevents false role completion and next model call',async()=>{
 const x=fakeEnv();const original=x.env.DB.prepare.bind(x.env.DB);
 x.env.DB.prepare=(sql)=>sql.startsWith('INSERT INTO schnapper_reports')
  ? {bind(){return {async run(){return {meta:{changes:0}}}}}}
  : original(sql);
 const out=await runSlot(x.env,Date.UTC(2026,9,22,21));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,1);
 assert.deepEqual(out.completed_roles,[]);
 assert.equal(x.getCalls(),1);
 assert.equal(x.db.reports.length,0);
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
});

test('D1 no-op completed status write must NOT return a success verdict',async()=>{
 const x=fakeEnv();const original=x.env.DB.prepare.bind(x.env.DB);
 x.env.DB.prepare=(sql)=>{
  if(!sql.startsWith('UPDATE schnapper_runs SET status='))return original(sql);
  const stmt=original(sql);
  return {bind(...args){
   if(args[0]==='completed')return {async run(){return {meta:{changes:0}}}};
   return stmt.bind(...args);
  }};
 };
 const out=await runSlot(x.env,Date.UTC(2026,9,22,22));
 assert.equal(x.getCalls(),4);
 assert.equal(x.db.reports.length,4);
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
});
