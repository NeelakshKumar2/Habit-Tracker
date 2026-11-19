'use strict';
  defineModule({id:'intentCard',kicker:'Your one thing',title:'Intent',span:6,render:function(){
  var it=state.profile.intent||{};
  if(!it.habit&&!it.dest){
    return '<p class="statement">Your most powerful self is waiting at the <em>most beautiful destination</em>.</p><p class="muted">Name the destination and the one habit that takes you there.</p><a class="btn" href="#habit" style="align-self:flex-start">Frame my intent</a>';
  }
  return (it.dest?'<p class="dest">'+esc(it.dest)+'</p>':'')+'<div class="kv">'+
    (it.habit?'<p><small>The one habit</small><span>'+esc(it.habit)+'</span></p>':'')+
    (it.when?'<p><small>When and where</small><span>'+esc(it.when)+'</span></p>':'')+
    (it.min?'<p><small>On hard days</small><span>'+esc(it.min)+'</span></p>':'')+'</div><a class="more" href="#habit">Refine</a>';
}});
