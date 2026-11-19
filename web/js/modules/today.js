'use strict';
  defineModule({id:'today',kicker:'Today',title:'Keep the chain',span:7,render:function(){
  var rows=liveRows();
  if(!rows.length){
    return '<p class="muted">Nothing is live today. Start a challenge and it will appear here for a one-tap check-in.</p><a class="btn primary" href="#challenges" style="align-self:flex-start">Start a challenge</a>';
  }
  var done=rows.filter(function(r){return r.c.ticks[r.s.t];}).length;
  return '<p class="meta">'+done+' of '+rows.length+' done today</p><div>'+rows.map(function(r){
    var on=!!r.c.ticks[r.s.t];
    return '<div class="trow"><a class="tname" href="#c-'+esc(r.c.id)+'"><b>'+esc(r.c.name)+'</b><span>Day '+(r.s.t+1)+' of '+r.c.days+'</span></a>'+
      '<button type="button" class="tickbtn'+(on?' on':'')+'" data-do="today.tick" data-cid="'+esc(r.c.id)+'" data-i="'+r.s.t+'" aria-pressed="'+on+'" aria-label="Mark today done for '+esc(r.c.name)+'">'+CHECK+'</button></div>';
  }).join('')+'</div>';
},actions:{tick:function(b){tickAt(b.getAttribute('data-cid'),parseInt(b.getAttribute('data-i'),10));}}});
