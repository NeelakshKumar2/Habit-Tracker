'use strict';
  defineModule({id:'glance',span:12,render:function(){
  var a=analyze();
  function g(n,l){return '<div class="gl"><span class="gn">'+n+'</span><small>'+l+'</small></div>';}
  return '<div class="glance">'+g(a.current,'Current streak')+g(a.longest,'Longest streak')+g(a.daysKept,'Days kept')+g(a.A.completed,'Completed')+'</div>';
}});
