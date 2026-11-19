'use strict';
  defineModule({id:'confidence',kicker:'Confident Self',title:'Confidence is evidence',span:6,render:function(){
  var a=analyze(),th=TIERS[CONFIDENT].min;
  if(a.score>=th){
    return '<div class="conf on"><h3>Unlocked</h3><p class="muted">This is not a mood. It is a record. You have the proof.</p>'+
      '<div class="proof"><span><b>'+a.daysKept+'</b> days kept</span><span><b>'+a.A.completed+'</b> challenges finished</span><span><b>'+a.longest+'</b> day best streak</span></div></div>';
  }
  return '<div class="conf"><h3>'+(th-a.score)+' points to go</h3><div class="bar2" aria-hidden="true"><i style="width:'+Math.round(a.score/th*100)+'%"></i></div>'+
    '<p class="muted">Past '+th+', the evidence outweighs the doubt. Every tick, finished challenge and written note adds to it. A finished 90-day challenge with notes gets you there.</p></div>';
}});
