'use strict';
/* Module: where the grit score comes from. */
defineModule({id:'breakdown',kicker:'Score',title:'How your grit is built',span:6,render:function(){
  var a=analyze(),p=a.pts,max=Math.max(1,p.show,p.finish,p.streak,p.reflect);
  function row(l,v){return '<div class="brow"><span>'+l+'</span><div class="bar2" aria-hidden="true"><i style="width:'+Math.round(v/max*100)+'%"></i></div><b>'+v+'</b></div>';}
  return '<div>'+row('Days kept',p.show)+row('Finishing',p.finish)+row('Streak',p.streak)+row('Reflection',p.reflect)+'</div>'+
    '<div class="mult"><span>Consistency <b>'+Math.round(a.cons*100)+'%</b></span><span>Recency <b>'+Math.round(a.rec*100)+'%</b></span><span>Score <b>'+a.score+'</b></span></div>'+
    '<p class="meta">Points are scaled by how many of the days that have passed you actually kept, and by how recently you showed up.</p>';
}});
