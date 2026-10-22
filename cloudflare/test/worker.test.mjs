import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import worker,{runSlot,verifyGate,MODEL,ROLES,utcSlot} from '../src/worker.mjs';
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
test('Fail-closed when Free tier unverified',async()=>{const x=fakeEnv({ACCOUNT_FREE_PLAN_CONFIRMED:'no'});assert.equal(verifyGate(x.env),false);assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Disabled switch prohibits inference',async()=>{const x=fakeEnv({RUN_ENABLED:'false'});assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Wrong policy prohibits inference',async()=>{const x=fakeEnv({COST_POLICY:'paid'});assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Valid slot four real invocations (mocked), four hashes and audit',async()=>{const x=fakeEnv();const t=Date.UTC(2026,9,22,4,17);const o=await runSlot(x.env,t);assert.equal(o.status,'ABGESCHLOSSEN');assert.equal(o.attempted_calls,4);assert.deepEqual(o.roles.map(r=>r.role),ROLES);assert.equal(x.db.reports.length,4);assert.equal(x.db.audit.length,4);assert.equal(x.db.statuses[0][0],'completed');assert.equal(x.db.reports[0][4].length,64);assert.equal((await runSlot(x.env,t+1000)).status,'BEREITS_VERSUCHT');assert.equal(x.getCalls(),4);});
test('Capacity failure records interrupted role and refuses retry',async()=>{const x=fakeEnv();let calls=0;x.env.AI.run=async()=>{calls++;if(calls===2)throw Error('Free quota exhausted');return {response:'eins'};};const t=Date.UTC(2026,9,22,7);const out=await runSlot(x.env,t);assert.equal(out.status,'BLOCKIERT');assert.equal(out.attempted_calls,2);assert.deepEqual(out.completed_roles,['LEAD']);assert.equal(x.db.statuses.at(-1)[0],'blocked');assert.equal((await runSlot(x.env,t)).status,'BEREITS_VERSUCHT');assert.equal(calls,2);});
test('Bad AI response blocks without fabricated report',async()=>{const x=fakeEnv();x.env.AI.run=async()=>({response:''});assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,10))).status,'BLOCKIERT');assert.equal(x.db.reports.length,0);});
test('No database or schema means zero calls',async()=>{const x=fakeEnv({DB:{prepare(){throw Error('no schema');}}});assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,3))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('DB audit failure before inference prevents charges',async()=>{const x=fakeEnv();const original=x.env.DB.prepare;x.env.DB.prepare=(sql)=>{if(sql.startsWith('UPDATE schnapper_runs SET attempted_calls='))throw Error('D1 down');return original(sql);};assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,3))).status,'BLOCKIERT');assert.equal(x.getCalls(),0);});
test('Persistent emergency stop blocks all model calls',async()=>{
 const x=fakeEnv();x.db.control.paused=1;
 const out=await runSlot(x.env,Date.UTC(2026,9,22,13));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,0);
 assert.equal(x.getCalls(),0);
 assert.equal(x.db.slots.size,0);
});
test('D1 emergency stop read error fails closed',async()=>{
 const x=fakeEnv();x.db.control.readFails=true;
 const out=await runSlot(x.env,Date.UTC(2026,9,22,14));
 assert.equal(out.status,'BLOCKIERT');assert.equal(x.getCalls(),0);
});
test('Emergency stop in the middle of a run blocks all next calls',async()=>{
 const x=fakeEnv();let calls=0;
 x.env.AI.run=async()=>{
  calls++;
  if(calls===1)x.db.control.paused=1;
  return {response:'Abgeschlossene Antwort'};
 };
 const out=await runSlot(x.env,Date.UTC(2026,9,22,15));
 assert.equal(out.status,'BLOCKIERT');
 assert.equal(out.attempted_calls,1);
 assert.deepEqual(out.completed_roles,['LEAD']);
 assert.equal(calls,1);
 assert.equal(x.db.statuses.at(-1)[0],'blocked');
});
test('Malformed timestamps not accepted',async()=>{const x=fakeEnv();assert.equal((await runSlot(x.env,'not-a-date')).status,'BLOCKIERT');assert.equal(x.getCalls(),0);assert.equal(utcSlot(Date.UTC(2026,9,22,4,17)),'2026102204');});
test('HTTP does not expose private reports',async()=>{assert.equal((await worker.fetch()).status,404);});
