'use strict';
/* Module: all your challenges as cards. */
defineModule({id:'challengeList',kicker:'Library',title:'Your challenges',span:7,render:function(){
  if(!state.items.length){
    return '<div class="empty">No challenges yet. Name one, pick a length and press Start challenge.</div>';
  }
  return '<div class="list">'+state.items.map(function(c){
    var s=stats(c),st=statusOf(c),pct=Math.round(s.done/c.days*100);
    return '<a class="card" href="#c-'+esc(c.id)+'"><div class="card-top"><h3>'+esc(c.name)+'</h3><span class="chip '+st.cls+'">'+esc(st.label)+'</span></div>'+
      '<p class="meta">'+plural(c.days,'day')+' · '+esc(fShort(c.start))+' to '+esc(fEnd(c.start,s.end))+'</p>'+
      '<div class="bar2" aria-hidden="true"><i style="width:'+pct+'%"></i></div>'+
      '<p class="meta">'+s.done+' of '+c.days+' days done</p></a>';
  }).join('')+'</div>';
}});
