/** Direct competition inventory + full message text, bypassing global keyword search.
 * Receipts retain hashes and matched climate context only, never unrelated bodies.
 */
import {createHash} from 'node:crypto';
const digest = value => createHash('sha256').update(value).digest('hex');
const climate = /(?:\bweather\b|climat|\bforecast\w*|\bhazard\b|wind_exposure_index|wildfire_index|hail_days|freezing_days|rainfall_mm|mean_temperature_c|dry_summer_index|\bwind\b|\bwildfire\b|\bhail\b|\brainfall\b|\btemperatur\w*|\bviento\b|pron[oó]stic)/i;
const temporal = /(?:\benvironment\w*|\bmeteorolog\w*|\bfuture\b|\bknown\b|\bin advance\b|\bas.of\b|point.in.time|(?:availab\w*|information|data).{0,70}(?:quot|inception|start of|beginning)|(?:quot|inception|start of|beginning).{0,70}(?:availab\w*|known|information))/i;
const requireCondition = (condition, message) => {if (!condition) throw new Error(message);};

export function reviewCorpus(inventories, records, control={topicId:751543, query:'Claims Data Query'}) {
  const expected = new Map();
  for (const inventory of inventories) {
    const rows=inventory.topics;
    requireCondition(Array.isArray(rows) && rows.length===Number(inventory.total_count),'Incomplete topic inventory');
    for (const row of rows) {
      requireCondition(!expected.has(row.id),'Duplicate inventory topic');
      expected.set(row.id,{...row,part:inventory.part,slug:inventory.slug});
    }
  }
  requireCondition(records.length===expected.size,'Missing topic response');
  const seen=new Set(); const indexed=[]; const matches=[]; const temporalMatches=[];
  let positive=false; let rootCount=0; let replyCount=0;
  for(const record of records) {
    const entry=expected.get(record.topic_id);
    requireCondition(entry && !seen.has(record.topic_id),'Unexpected or duplicate topic response');
    seen.add(record.topic_id);
    const prefix='/competitions/'+entry.slug;
    requireCondition(record.response_parent_url===prefix && record.response_url.startsWith(prefix+'/discussion/'+entry.id),'Wrong competition/topic URL');
    const ids=new Set();
    for(const message of record.messages) {
      requireCondition(Number.isInteger(message.id) && !ids.has(message.id),'Duplicate message ID');
      ids.add(message.id);
      requireCondition(typeof message.raw_markdown==='string' && message.raw_markdown.trim().length>0,'Empty message body');
    }
    requireCondition(ids.has(record.root_id),'Missing root body');
    const replies=ids.size-1;
    requireCondition(replies===Number(entry.comment_count??0) && replies===Number(record.server_total_messages??0),'Incomplete comments');
    const title=String(record.topic_title??'');
    if(entry.id===control.topicId && (title+'\n'+record.messages.map(x=>x.raw_markdown).join('\n')).toLowerCase().includes(control.query.toLowerCase()))positive=true;
    indexed.push({part:entry.part,topic_id:entry.id,root_id:record.root_id,listed_replies:Number(entry.comment_count??0),server_replies:Number(record.server_total_messages??0),received_replies:replies,title_sha256:digest(title),canonical_source_sha256:digest(JSON.stringify(record)),messages:record.messages.map(m=>({id:m.id,utc:m.utc,author:m.author,author_type:m.author_type,characters:m.raw_markdown.length,body_sha256:digest(m.raw_markdown)}))});
    for(const message of record.messages) {
      const source={part:entry.part,topic_id:entry.id,message_id:message.id,utc:message.utc,author:message.author,author_type:message.author_type};
      if(climate.test(title+'\n'+message.raw_markdown))matches.push({...source,body:message.raw_markdown});
      if(temporal.test(message.raw_markdown))temporalMatches.push({...source,body:message.raw_markdown});
    }
    rootCount++;replyCount+=replies;
  }
  requireCondition(positive,'Positive control not found');
  const impossible='F05_CONTROL_NEGATIVO_20261024_NO_ES_UN_ANUNCIO';
  requireCondition(!records.some(r=>(r.topic_title+'\n'+r.messages.map(m=>m.raw_markdown).join('\n')).includes(impossible)),'Negative-control string unexpectedly present');
  return {method:'list_competition_topics → get_forum_topic(includeComments,100) → local full-message matching',topics:seen.size,roots:rootCount,replies:replyCount,messages:rootCount+replyCount,positive_control:{...control,found:true},negative_control:{query:impossible,found:false},indexed,climate_matches:matches,temporal_context_matches:temporalMatches,scope:'Bodies searched in memory. Only matching context and source hashes retained; no universal absence or remote-search repair claimed.'};
}

export function checkGuards(inventories,records) {
  const failures=[];
  function rejects(label,mutate) {
    const r=structuredClone(records);mutate(r);
    let rejected=false;
    try {reviewCorpus(inventories,r);} catch {rejected=true;}
    requireCondition(rejected,'Guard failed: '+label);failures.push({case:label,rejected});
  }
  rejects('missing topic',r=>r.pop());
  rejects('wrong market URL',r=>r[0].response_parent_url='/competitions/unrelated');
  rejects('missing reply',r=>{const x=r.find(y=>y.messages.length>1);x.messages=x.messages.filter(m=>m.id===x.root_id);});
  rejects('duplicate message',r=>r[0].messages.push(r[0].messages[0]));
  return {scope:'New retrieval/coverage guards only; no numerical model diagnostics',cases:failures};
}
