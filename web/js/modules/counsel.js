'use strict';
  defineModule({id:'counsel',kicker:'Counsel of the day',span:12,render:function(){
  var w=WISDOM[Math.floor(dayNo(today()))%WISDOM.length];
  return '<p class="quote">'+esc(w.idea)+'</p><p class="qsrc"><span class="chip">'+(w.kind==='book'?'Book':'Scripture')+'</span><span>'+esc(w.src)+' · '+esc(w.by)+'</span></p><a class="more" href="#wisdom">More wisdom</a>';
}});
