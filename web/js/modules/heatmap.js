'use strict';
/* Module: 20-week activity grid, Monday to Sunday. */
defineModule({id:'heatmap',kicker:'Consistency',title:'The last 20 weeks',span:12,render:function(){
  var a=analyze(),tk=today(),W=20;
  var dowToday=(parseKey(tk).getDay()+6)%7;
  var start=addDays(tk,-(dowToday+7*(W-1)));
  var cells='',w,d;
  for(w=0;w<W;w++){for(d=0;d<7;d++){
    var k=addDays(start,w*7+d),n=a.ticked[k]||0,lvl=n>=3?3:n;
    cells+='<i class="hc l'+lvl+(k>tk?' fut':'')+'" title="'+esc(fShort(k))+': '+n+(n===1?' day':' days')+' ticked"></i>';
  }}
  var labs=['Mon','','Wed','','Fri','',''].map(function(t){return '<span>'+t+'</span>';}).join('');
  return '<div class="heatwrap"><div class="heatlab" aria-hidden="true">'+labs+'</div><div class="heat" role="img" aria-label="Activity grid for the last 20 weeks">'+cells+'</div></div>'+
    '<div class="hkey"><span>Less</span><i class="hc"></i><i class="hc l1"></i><i class="hc l2"></i><i class="hc l3"></i><span>More</span></div>';
}});
