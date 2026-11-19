'use strict';
/* Module: one row of performance per challenge. */
defineModule({id:'perf',kicker:'Challenges',title:'Performance',span:12,render:function(){
  if(!state.items.length)return '<div class="empty">Start a challenge to see how it performs.</div>';
  return '<div>'+state.items.map(function(c){
    var s=stats(c),st=statusOf(c),el=Math.max(1,Math.min(c.days,s.t+1)),rate=s.notStarted?0:Math.round(s.done/el*100);
    return '<div class="prow"><b>'+esc(c.name)+'</b><div class="bar2" aria-hidden="true"><i style="width:'+Math.round(s.done/c.days*100)+'%"></i></div>'+
      '<span>'+s.done+' / '+c.days+'</span><span>'+rate+'% kept</span><span class="chip '+st.cls+'">'+esc(st.label)+'</span></div>';
  }).join('')+'</div>';
}});
