'use strict';
/* Module: which weekdays you keep best. */
var FULLDOW=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
defineModule({id:'weekday',kicker:'Pattern',title:'Strongest days',span:6,render:function(){
  var a=analyze(),counts=[0,0,0,0,0,0,0];
  Object.keys(a.ticked).forEach(function(k){counts[(parseKey(k).getDay()+6)%7]++;});
  var max=Math.max.apply(null,counts),best=max>0?counts.indexOf(max):-1;
  return '<div class="wk" role="img" aria-label="Days kept by weekday">'+counts.map(function(n,i){
    var h=max?Math.round(n/max*100):0;
    return '<div class="wkc"><b>'+n+'</b><div class="wkbar"><i'+(i===best?' class="top"':'')+' style="height:'+h+'%"></i></div><span>'+DOW[i]+'</span></div>';
  }).join('')+'</div>'+
  '<p class="meta">'+(best>=0?'You are strongest on '+FULLDOW[best]+'s. Guard the weaker days first.':'Tick a few days and your pattern will show here.')+'</p>';
}});
