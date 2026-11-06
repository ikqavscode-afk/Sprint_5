const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const load=n=>fetch('data/'+n).then(r=>r.json());
const REPO='https://github.com/ikqavscode-afk/Sprint_5';
const mb=m=>m?`<span class="m ${m}">${m}</span>`:'';
const sp=c=>c==null?'':`<span class="sp s${String(c)[0]}">${c}</span>`;
const toast=t=>{let e=$('#toast');if(!e){e=document.createElement('div');e.id='toast';e.className='toast';document.body.appendChild(e)}e.textContent=t;e.classList.add('on');setTimeout(()=>e.classList.remove('on'),1400)};
const copy=t=>navigator.clipboard.writeText(t).then(()=>toast('Скопировано'));
const NAV=[['index.html','◧','Обзор'],['explorer.html','☰','Чек-лист API'],['bugs.html','✖','Реестр дефектов'],['playground.html','▶','Песочница контракта'],['gray-zones.html','◐','Серые зоны'],['places.html','⚙','Разбор API: Places'],['learn.html','✎','Шпаргалка и квиз'],['checklist.html','✔','Чек-лист тестировщика'],['files.html','⇩','Файлы: Postman, OpenAPI']];
function shell(path){
  const cur=location.pathname.split('/').pop()||'index.html';
  $('aside').innerHTML=`<div class="logo">{ <b>api</b> }<small>Прилавок · тестирование</small></div>`+
   NAV.map(([h,i,t])=>`<a class="nav ${h===cur?'on':''}" href="${h}"><span class="mono">${i}</span>${t}</a>`).join('')+
   `<div class="grow"></div><div class="sep"></div><div class="foot"><a href="${REPO}">GitHub: Sprint_5 ↗</a><button id="theme">◐ Тема</button></div>`;
  $('#theme').onclick=()=>{const t=document.documentElement.dataset.theme==='light'?'dark':'light';document.documentElement.dataset.theme=t;localStorage.setItem('theme',t)};
  if(path)$('.path').innerHTML=`~/prilavok/<b>${path}</b>`;
  document.addEventListener('keydown',e=>{if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){const q=$('input[type=search]');if(q){e.preventDefault();q.focus()}}});
}
const CLS={'validation-missing':'200 вместо 4xx','unhandled-500':'500 вместо 400','incomplete-response':'неполное тело','wrong-status':'неверный код'};
const AREA={'kits':'Наборы','delivery':'Доставка','orders-put':'Корзина PUT','orders-get':'Корзина GET','orders-delete':'Корзина DELETE'};
