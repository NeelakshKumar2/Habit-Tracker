'use strict';
/* Module: weekly review. Asks the Grit server (/api/review) for a short, rule-based read of your streak,
   consistency and weakest day. It is plain arithmetic on your own data. Runs on the server for your account. */
(function(){
  var R={loading:false,data:null,error:''};
  defineModule({id:'review',kicker:'Review',title:'Weekly review',span:12,
    render:function(){
      if(R.loading)return '<p class="muted">Reviewing your week...</p>';
      var d=R.data,btn='<button type="button" class="btn'+(d?'':' primary')+'" data-do="review.ask" style="align-self:flex-start">'+(d?'Review again':'Review my week')+'</button>';
      if(R.error)return '<p class="muted">'+esc(R.error)+'</p>'+btn;
      if(!d)return '<p class="muted">Get a short, specific review of your streak, consistency and weakest day.</p>'+btn;
      return '<p class="review-h">'+esc(d.headline)+'</p>'+
        '<ul class="review-list">'+d.insights.map(function(t){return '<li>'+esc(t)+'</li>';}).join('')+'</ul>'+
        '<p class="review-next"><small>Next step</small>'+esc(d.next_step)+'</p>'+btn;
    },
    actions:{ask:function(){
      R.loading=true;R.error='';refresh();
      Api.req('GET','/api/review').then(function(r){R.data=r;}).catch(function(){R.error='The review could not be loaded. Check your connection and try again.';})
        .then(function(){R.loading=false;refresh();});
    }}
  });
})();
