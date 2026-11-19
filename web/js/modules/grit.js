'use strict';
  defineModule({id:'grit',kicker:'Standing',title:'Grit score',span:5,render:function(){
  var a=analyze(),T=TIERS[a.tier],N=a.next;
  var C=2*Math.PI*68,dash=(C*Math.min(1,a.score/1000)).toFixed(1);
  var ring='<svg class="ring" viewBox="0 0 160 160" role="img" aria-label="Grit score '+a.score+' of 1000"><g transform="rotate(-90 80 80)">'+
    '<circle cx="80" cy="80" r="68" fill="none" stroke="var(--line2)" stroke-width="3"/>'+
    (a.score>0?'<circle cx="80" cy="80" r="68" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linecap="round" stroke-dasharray="'+dash+' '+C.toFixed(1)+'"/>':'')+
    '<g transform="rotate('+(TIERS[CONFIDENT].min/1000*360)+' 80 80)"><line x1="140" y1="80" x2="154" y2="80" stroke="var(--signal)" stroke-width="2.5"/></g></g>'+
    '<text x="80" y="88" text-anchor="middle" class="rnum">'+a.score+'</text><text x="80" y="108" text-anchor="middle" class="rsub">OF 1000</text></svg>';
  var next=N?'<div class="bar2" aria-hidden="true"><i style="width:'+Math.round(a.pct*100)+'%"></i></div><p class="meta">'+(N.min-a.score)+' points to '+esc(N.name)+'</p>':'<p class="meta">The highest tier. Hold it.</p>';
  return '<div class="gritbox">'+ring+'<div class="gtext"><p class="kick">Tier</p><p class="tier">'+esc(T.name)+'</p><p class="tline">'+esc(T.line)+'</p>'+next+'</div></div>'+
    '<a class="more" href="#insights">See how it is built</a>';
}});
