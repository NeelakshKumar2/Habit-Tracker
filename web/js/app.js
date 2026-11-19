'use strict';
/* App shell: navigation, routing, rendering, event dispatch and boot. */
var app=document.getElementById('app');
function val(v){return typeof v==='function'?v():(v||'');}

function updateNav(){
  var list=PAGES.filter(function(p){return p.nav!==false;});
  var html=list.map(function(p){
    var on=state.page===p.id;
    return '<a href="#'+esc(p.id)+'"'+(on?' aria-current="page"':'')+'>'+icon(p.icon)+'<span>'+esc(p.label)+'</span></a>';
  }).join('');
  $('#tabs').innerHTML=html;$('#dock').innerHTML=html;$('#dock').style.setProperty('--n',list.length);
  var chip=$('#mechip');
  if(chip){
    chip.innerHTML=state.ready?avatarHTML('chip'):'';
    if(state.page==='account')chip.setAttribute('aria-current','page');else chip.removeAttribute('aria-current');
  }
}
function renderPage(){
  var pg=pageById(state.page)||PAGES[0];
  if(!state.ready){app.innerHTML='<p class="muted">'+(state.stale?'Could not reach your saved data. Refresh to try again.':'Opening '+BRAND+'...')+'</p>';return;}
  var txt='<div><p class="eyebrow">'+esc(val(pg.eyebrow))+'</p><h1>'+esc(val(pg.title))+'</h1>'+(pg.sub?'<p class="sub">'+esc(val(pg.sub))+'</p>':'')+'</div>';
  var head=pg.header===false?'':(pg.id==='home'?'<div class="phead has-av"><a class="av-hero" href="#account" aria-label="Your account">'+avatarHTML('hero')+'</a>'+txt+'</div>':'<div class="phead">'+txt+'</div>');
  app.innerHTML=head+'<div class="mods">'+pg.modules.map(function(id){return modHTML(id);}).join('')+'</div>';
}
function buildView(){if(state.view==='challenge')buildChallenge();else renderPage();}
function route(){
  var h=location.hash.replace(/^#/,'');
  if(h.indexOf('c-')===0){state.view='challenge';state.cid=h.slice(2);state.page='challenges';}
  else{var pg=pageById(h)||PAGES[0];state.view='page';state.page=pg.id;state.cid=null;}
  if(state.page!=='challenges')state.prefill=null;
  state.sel=null;state.confirmDel=false;
  updateNav();buildView();window.scrollTo(0,0);
}
function refresh(){
  updateNav();
  if(state.view==='challenge'){
    var c=curChallenge();
    if(!c){if(state.ready)buildChallenge();return;}
    if(!$('#grid')){buildChallenge();return;}
    updateChallenge();return;
  }
  var ae=document.activeElement;
  if(ae&&app.contains(ae)&&/^(INPUT|TEXTAREA)$/.test(ae.tagName)&&ae.type!=='file')return;
  renderPage();
}

/* Event dispatch: modules own their events through `actions` (data-do) and `on`. */
function modOf(el){var s=el.closest('[data-mod]');return s?MODULES[s.getAttribute('data-mod')]:null;}
app.addEventListener('click',function(e){
  var d=e.target.closest('[data-do]');
  if(d){var p=d.getAttribute('data-do').split('.'),m=MODULES[p[0]];if(m&&m.actions&&m.actions[p[1]])m.actions[p[1]](d,e);return;}
  var a=e.target.closest('[data-act]');if(a)challengeClick(a);
});
['submit','input','change'].forEach(function(type){
  app.addEventListener(type,function(e){
    var m=modOf(e.target);if(m&&m.on&&m.on[type])m.on[type](e);
    if(type==='input')challengeInput(e.target);
  });
});
window.addEventListener('hashchange',route);

function boot(){
  route();
  Api.req('GET','/api/auth/me').then(function(r){
    state.user=r.user;backend=apiBackend();setFoot();
    try{localStorage.setItem('gritForgeIn','1');}catch(e){}
    return backend.start();
  }).catch(function(e){
    if(e&&e.status===401)return;
    state.stale=true;renderPage();toast('Could not reach '+BRAND+'. Check your connection and refresh.');
  });
}
boot();
