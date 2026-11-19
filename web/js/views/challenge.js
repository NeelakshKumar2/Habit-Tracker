'use strict';
/* View: one challenge (calendar, day panel, notes). Reached at #c-<id>. */
function curChallenge(){for(var i=0;i<state.items.length;i++){if(state.items[i].id===state.cid)return state.items[i];}return null;}
function selIdx(c){
  if(state.sel!=null&&state.sel<c.days)return state.sel;
  var s=stats(c);return Math.min(Math.max(s.t,0),c.days-1);
}
function buildChallenge(){
  if(!state.ready){app.innerHTML='<a class="back" href="#challenges">All challenges</a><div class="empty">'+(state.stale?'Still trying to reach your saved challenges.':'Opening your calendar...')+'</div>';return;}
  var c=curChallenge();
  if(!c){app.innerHTML='<a class="back" href="#challenges">All challenges</a><div class="empty">This challenge was not found. It may have been deleted.</div>';return;}
  app.innerHTML='<a class="back" href="#challenges">All challenges</a><section class="head" id="head"></section>'+
    '<div class="layout"><section class="box day" id="panel"></section>'+
    '<div id="left"><div class="dow" aria-hidden="true">'+DOW.map(function(d){return '<span>'+d+'</span>';}).join('')+'</div><div class="grid" id="grid"></div>'+
    '<div class="key"><span><i class="k-done"></i>Done</span><span><i class="k-miss"></i>Missed</span><span><i class="k-today"></i>Today</span></div>'+
    '<section class="journal" id="journal"></section></div></div>';
  updateChallenge();
}
function updateChallenge(){renderHead();renderGrid();renderPanel();renderJournal();}
function renderHead(){
  var c=curChallenge(),el=$('#head');if(!c||!el)return;
  var s=stats(c),pct=Math.round(s.done/c.days*100),b;
  if(s.complete)b='<div class="banner done"><strong>Challenge completed</strong>You ticked all '+c.days+' days from '+fShort(c.start)+' to '+fEnd(c.start,s.end)+'.</div>';
  else if(s.notStarted)b='<div class="banner"><strong>Challenge started</strong>'+plural(c.days,'day')+', '+fShort(c.start)+' to '+fEnd(c.start,s.end)+'. Day 1 begins in '+plural(-s.t,'day')+'.</div>';
  else if(s.ended)b='<div class="banner ended"><strong>Challenge ended</strong>You ticked '+s.done+' of '+c.days+' days. Missed days can still be ticked below.</div>';
  else b='<div class="banner"><strong>Challenge started</strong>'+plural(c.days,'day')+', '+fShort(c.start)+' to '+fEnd(c.start,s.end)+'. Today is day '+(s.t+1)+'.</div>';
  var del=state.confirmDel
    ?'<div class="confirm">Delete this challenge and its notes? <button class="btn danger ghost" data-act="del-yes" type="button">Delete</button><button class="btn ghost" data-act="del-no" type="button">Keep</button></div>'
    :'<button class="btn ghost" data-act="del-ask" type="button">Delete challenge</button>';
  el.innerHTML='<div class="head-row"><h1>'+esc(c.name)+'</h1>'+del+'</div>'+
    '<p class="range">'+plural(c.days,'day')+' · '+esc(fLong(c.start))+' to '+esc(fLong(s.end))+'</p>'+
    '<div class="prog"><div class="bar2" role="progressbar" aria-valuemin="0" aria-valuemax="'+c.days+'" aria-valuenow="'+s.done+'"><i style="width:'+pct+'%"></i></div><p><b>'+s.done+'</b> of '+c.days+' days done</p></div>'+b;
}
function renderGrid(){
  var c=curChallenge(),el=$('#grid');if(!c||!el)return;
  var s=stats(c),sel=selIdx(c),lead=(parseKey(c.start).getDay()+6)%7,h='',i;
  for(i=0;i<lead;i++)h+='<span></span>';
  for(i=0;i<c.days;i++){
    var k=addDays(c.start,i),d=parseKey(k),done=!!c.ticks[i],cls='cell';
    if(done)cls+=' done';else if(i<s.t)cls+=' missed';
    if(i>s.t)cls+=' future';
    if(i===s.t)cls+=' today';
    if(i===sel)cls+=' sel';
    var mo=(i===0||d.getDate()===1)?'<span class="mo">'+MON[d.getMonth()]+'</span>':'';
    h+='<button type="button" class="'+cls+'" data-act="pick" data-i="'+i+'" aria-label="Day '+(i+1)+', '+esc(fShort(k))+(done?', done':'')+'"'+(i===sel?' aria-current="true"':'')+'>'+
      mo+(i+1)+(done?'<svg class="ck" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3.2 3.2L13 4.8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>':'')+'</button>';
  }
  el.innerHTML=h;
}
function renderPanel(){
  var c=curChallenge(),el=$('#panel');if(!c||!el)return;
  if(document.activeElement&&document.activeElement.id==='note')return;
  var s=stats(c),i=selIdx(c),k=addDays(c.start,i);
  var head='<p class="eyebrow">Day '+(i+1)+' of '+c.days+'</p><h2>'+esc(fLong(k))+'</h2>';
  if(i>s.t){el.innerHTML=head+'<p class="muted">This day opens on '+esc(fShort(k))+'. Come back then to tick it and write a note.</p>';return;}
  var done=!!c.ticks[i],isToday=(i===s.t);
  var dk=c.id+':'+i,text=(state.drafts[dk]!=null)?state.drafts[dk]:(c.notes[i]||'');
  var n=words(text).length;
  var label=done?(isToday?'Today is done':'Day done'):(isToday?'Mark today done':'Mark this day done');
  el.innerHTML=head+'<button type="button" class="tick'+(done?' is-done':'')+'" data-act="tick" aria-pressed="'+done+'">'+CHECK+label+'</button>'+
    '<div class="notehead"><label for="note">Note for this day</label><span class="wc'+(n>=NOTE_MAX?' full':'')+'" id="wc">'+n+' / '+NOTE_MAX+' words</span></div>'+
    '<textarea id="note" rows="4" placeholder="What did you do, and how did it feel?">'+esc(text)+'</textarea>'+
    '<div class="row"><button type="button" class="btn" data-act="save">Save note</button></div>';
}
function renderJournal(){
  var c=curChallenge(),el=$('#journal');if(!c||!el)return;
  var rows=[],i;for(i=0;i<c.days;i++){if(c.notes[i])rows.push(i);}
  if(!rows.length){el.innerHTML='';return;}
  el.innerHTML='<h2 class="sect-title">Your notes</h2><ol>'+rows.map(function(i){
    return '<li><p class="jd">Day '+(i+1)+' · '+esc(fShort(addDays(c.start,i)))+'</p><p>'+esc(c.notes[i])+'</p></li>';
  }).join('')+'</ol>';
}
/* Tick or untick a day. Also used by the Today module. Announces tier changes. */
function tickAt(id,i){
  var cc=null;state.items.forEach(function(x){if(x.id===id)cc=x;});if(!cc)return;
  var c=clone(cc),s=stats(c);if(i>s.t||i<0)return;
  var before=analyze(),was=!!c.ticks[i];
  if(was)delete c.ticks[i];else c.ticks[i]=true;
  persist(c);
  if(was)return;
  var after=analyze();
  if(stats(c).complete)toast('Challenge completed. Grit score '+after.score+'.');
  else if(after.tier>before.tier&&after.tier>=CONFIDENT&&before.tier<CONFIDENT)toast('Confident Self unlocked. You earned it.');
  else if(after.tier>before.tier)toast('New tier: '+TIERS[after.tier].name+'. Grit score '+after.score+'.');
  else toast('Day '+(i+1)+' done. Grit score '+after.score+'.');
}
function saveNote(){
  var cc=curChallenge();if(!cc)return;
  var ta=$('#note');if(!ta)return;
  var c=clone(cc),i=selIdx(c),text=words(ta.value).slice(0,NOTE_MAX).join(' ');
  if(text)c.notes[i]=text;else delete c.notes[i];
  delete state.drafts[c.id+':'+i];
  persist(c);toast(text?'Note saved for day '+(i+1)+'.':'Note cleared.');
}
function challengeClick(b){
  var a=b.getAttribute('data-act'),c=curChallenge();
  if(a==='pick'){state.sel=parseInt(b.getAttribute('data-i'),10);var ta=$('#note');if(ta)ta.blur();renderGrid();renderPanel();}
  else if(a==='tick'){if(c)tickAt(c.id,selIdx(c));}
  else if(a==='save'){saveNote();}
  else if(a==='del-ask'){state.confirmDel=true;renderHead();}
  else if(a==='del-no'){state.confirmDel=false;renderHead();}
  else if(a==='del-yes'&&c){
    var id=c.id;
    state.items=state.items.filter(function(x){return x.id!==id;});
    enqueue(id,function(){return backend.remove(id);}).catch(function(){toast('Could not delete that.');});
    state.confirmDel=false;location.hash='challenges';toast('Challenge deleted.');
  }
}
function challengeInput(t){
  if(t.id!=='note')return;
  var w=words(t.value);
  if(w.length>NOTE_MAX){t.value=w.slice(0,NOTE_MAX).join(' ');w=words(t.value);}
  var c=curChallenge();if(c)state.drafts[c.id+':'+selIdx(c)]=t.value;
  var wc=$('#wc');wc.textContent=w.length+' / '+NOTE_MAX+' words';wc.classList.toggle('full',w.length>=NOTE_MAX);
}
