import test from 'node:test';
import assert from 'node:assert/strict';
import worker,{runSlot,verifyGate,MODEL,ROLES} from '../src/worker.mjs';

function fakeDB() {
  const slots = new Set();
  const reports = [];
  const statuses = [];
  return {
    slots, reports, statuses,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async run() {
              if (sql.startsWith('INSERT OR IGNORE')) {
                const already = slots.has(args[0]);
                if (!already) slots.add(args[0]);
                return {meta: {changes: already ? 0 : 1}};
              }
              if (sql.startsWith('INSERT INTO schnapper_reports')) {
                reports.push(args);
                return {meta: {changes: 1}};
              }
              if (sql.startsWith('UPDATE schnapper_runs')) {
                statuses.push(args);
                return {meta: {changes: 1}};
              }
              throw Error('Unexpected SQL');
            }
          };
        }
      };
    }
  };
}
function fakeEnv(overrides={}) {
  const db = fakeDB();
  let calls=0;
  const env={RUN_ENABLED:'true',ACCOUNT_FREE_PLAN_CONFIRMED:'yes',COST_POLICY:'free-only',DB:db,
    AI:{run:async (model,body)=>{calls++;assert.equal(model,MODEL);assert.ok(body.max_tokens<=180);return {response:'Ein sachlicher Planungsvorschlag '+calls};}},
    ...overrides};
  return {env,db,getCalls:()=>calls};
}
test('safety gate blocks entirely when free plan unverified',async()=>{
  const x=fakeEnv({ACCOUNT_FREE_PLAN_CONFIRMED:'no'});
  assert.equal(verifyGate(x.env),false);
  assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');
  assert.equal(x.getCalls(),0);
  assert.equal(x.db.slots.size,0);
});
test('closed switch blocks even when binding present',async()=>{
  const x=fakeEnv({RUN_ENABLED:'false'});
  assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,4))).status,'BLOCKIERT');
  assert.equal(x.getCalls(),0);
});
test('enabled slot generates four distinct role reports and hashes, no repeat',async()=>{
  const x=fakeEnv();
  const t=Date.UTC(2026,9,22,4,17);
  const out=await runSlot(x.env,t);
  assert.equal(out.status,'ABGESCHLOSSEN');
  assert.equal(out.calls,4);
  assert.deepEqual(out.agenten.map(x=>x.role),ROLES);
  assert.equal(x.db.reports.length,4);
  assert.equal(x.db.statuses[0][0],'completed');
  assert.equal(x.db.reports[0][4].length,64);
  const second=await runSlot(x.env,t+1000);
  assert.equal(second.status,'BEREITS_VERSUCHT');
  assert.equal(x.getCalls(),4);
});
test('failed second inference records blocked and refuses retry',async()=>{
  const x=fakeEnv();let n=0;
  x.env.AI.run=async()=>{n++;if(n===2)throw Error('daily free allocation exhausted');return {response:'eins'};};
  const t=Date.UTC(2026,9,22,7);
  const a=await runSlot(x.env,t);
  assert.equal(a.status,'BLOCKIERT');
  assert.deepEqual(a.completed_roles,['LEAD']);
  assert.equal(x.db.statuses.at(-1)[0],'blocked');
  assert.equal((await runSlot(x.env,t)).status,'BEREITS_VERSUCHT');
  assert.equal(n,2);
});
test('invalid AI response does not count as work',async()=>{
  const x=fakeEnv();x.env.AI.run=async()=>({response:''});
  const out=await runSlot(x.env,Date.UTC(2026,9,22,10));
  assert.equal(out.status,'BLOCKIERT');
  assert.equal(x.db.reports.length,0);
});
test('missing database means zero model calls',async()=>{
  const x=fakeEnv({DB:{prepare(){throw Error('schema missing');}}});
  assert.equal((await runSlot(x.env,Date.UTC(2026,9,22,3))).status,'BLOCKIERT');
  assert.equal(x.getCalls(),0);
});
test('never publish internal reports through HTTP',async()=>{
  const result=await worker.fetch();
  assert.equal(result.status,404);
});
