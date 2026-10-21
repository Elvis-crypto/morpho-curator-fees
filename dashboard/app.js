const usd=v=>v==null?'–':'$'+Number(v).toLocaleString('en-US',{maximumFractionDigits:0});
const num=(v,d=4)=>Number(v).toLocaleString('en-US',{maximumFractionDigits:d});
const get=n=>fetch(`data/${n}.json`).then(r=>r.json());
const COL=['#4c8dff','#3ecf8e','#f5a524','#c084fc','#ff6b6b'];
Chart.defaults.color='#8a919c';Chart.defaults.borderColor='#22262d';
function table(el,cols,rows){el.innerHTML='<tr>'+cols.map(c=>`<th class="${c.t?'t':''}">${c.h}</th>`).join('')+'</tr>'+
  rows.map(r=>'<tr>'+cols.map(c=>`<td class="${c.t?'t':''} ${c.cls?c.cls(r):''}">${c.f?c.f(r[c.k],r):r[c.k]}</td>`).join('')+'</tr>').join('')}
Promise.all(['vault_daily','curator_daily','totals','recon_ledger','recon_summary'].map(get)).then(([vd,cd,tot,led,rs])=>{
  const sum=k=>tot.reduce((a,r)=>a+r[k],0), days=[...new Set(vd.map(r=>r.day))];
  document.getElementById('kpis').innerHTML=[['Fees',usd(sum('fees_usd'))],['Supply-side fees',usd(sum('fees_supply_side_usd'))],['Revenue (curators)',usd(sum('revenue_usd'))],['Period',`${days[0]} → ${days.at(-1)}`]]
    .map(([l,v])=>`<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div></div>`).join('');
  const curs=[...new Set(cd.map(r=>r.curator_name))]; let cc;
  const drawCur=m=>{cc&&cc.destroy();cc=new Chart(document.getElementById('curatorChart'),{type:'line',data:{labels:days,
    datasets:curs.map((c,i)=>({label:c,data:days.map(d=>(cd.find(r=>r.day==d&&r.curator_name==c)||{})[m]),borderColor:COL[i],pointRadius:0,tension:.2}))},
    options:{interaction:{mode:'index',intersect:false},scales:{y:{ticks:{callback:usd}}}}})};
  drawCur('fees_usd');document.getElementById('metric').onchange=e=>drawCur(e.target.value);
  const vs=[...new Set(vd.map(r=>r.name))],ds=[];
  vs.forEach((v,i)=>{const g=d=>vd.find(r=>r.day==d&&r.name==v)||{};
    ds.push({label:v+' · supply-side',data:days.map(d=>g(d).fees_supply_side_usd),backgroundColor:COL[i]+'aa',stack:v});
    ds.push({label:v+' · revenue',data:days.map(d=>g(d).revenue_usd),backgroundColor:COL[i],stack:v})});
  new Chart(document.getElementById('vaultChart'),{type:'bar',data:{labels:days,datasets:ds},options:{scales:{x:{stacked:true},y:{stacked:true,ticks:{callback:usd}}}}});
  table(document.getElementById('totals'),[{h:'Vault',k:'name',t:1},{h:'Curator',k:'curator_name',t:1},{h:'Days',k:'n_days'},{h:'Fees',k:'fees_usd',f:usd},{h:'Supply-side',k:'fees_supply_side_usd',f:usd},{h:'Revenue',k:'revenue_usd',f:usd}],tot);
  document.getElementById('rday').textContent=(led[0]||{}).day||'';
  table(document.getElementById('recon'),[{h:'Vault',k:'name',t:1},{h:'Ledger end',k:'ledger_end',f:v=>num(v)},{h:'On-chain end',k:'onchain_end',f:v=>num(v)},{h:'Diff',k:'diff',f:v=>num(v,8),cls:r=>r.diff==0?'ok':'bad'}],rs);
  table(document.getElementById('ledger'),[{h:'Vault',k:'name',t:1},{h:'Block',k:'block_number'},{h:'Event',k:'event',t:1},{h:'Tx',k:'tx_hash',t:1,f:v=>`<a href="https://etherscan.io/tx/${v}">${v.slice(0,10)}…</a>`},{h:'Δ assets',k:'delta_assets',f:v=>num(v)},{h:'Interest',k:'interest_assets',f:v=>num(v)},{h:'Curator fee',k:'curator_fee_assets',f:v=>num(v)},{h:'Running total',k:'running_last_total_assets',f:v=>num(v,2)}],led);
});
