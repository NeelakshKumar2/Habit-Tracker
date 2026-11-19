'use strict';
/* Modules for the Habit page: the hero statement, the one-thing builder and the habit loop. */
(function(){
  function readIntent(){
    function v(id,n){var e=$('#'+id);return e?e.value.trim().slice(0,n):'';}
    return {dest:v('i-dest',200),who:v('i-who',80),habit:v('i-habit',80),when:v('i-when',100),min:v('i-min',100)};
  }
  defineModule({id:'intentHero',span:12,bare:true,render:function(){
    var it=state.profile.intent||{};
    return '<p class="hero-statement">Your most powerful self is waiting at the <em>most beautiful destination</em>.</p>'+
      (it.dest?'<p class="dest">'+esc(it.dest)+'</p>':'')+
      (it.who?'<p class="muted">I am becoming someone who '+esc(it.who)+'.</p>':'');
  }});
  defineModule({id:'intentBuilder',kicker:'One thing',title:'Frame your intent',span:7,render:function(){
    var it=state.profile.intent||{};
    function f(id,label,val,ph,max){return '<div class="field"><label for="'+id+'">'+label+'</label><input type="text" id="'+id+'" maxlength="'+max+'" placeholder="'+esc(ph)+'" value="'+esc(val||'')+'" autocomplete="off"></div>';}
    return '<form id="intentForm" novalidate>'+
      '<div class="field"><label for="i-dest">My most beautiful destination</label><textarea id="i-dest" rows="3" maxlength="200" placeholder="Describe the place your most powerful self is waiting.">'+esc(it.dest||'')+'</textarea></div>'+
      f('i-who','I am becoming someone who',it.who,'shows up before anyone is watching',80)+
      f('i-habit','The one habit that gets me there',it.habit,'Walk for 30 minutes',80)+
      f('i-when','When and where',it.when,'After my first coffee, outside my door',100)+
      f('i-min','Two-minute version for hard days',it.min,'Put on my shoes and step outside',100)+
      '<div class="row"><button class="btn primary" type="submit">Save intent</button>'+
      '<button class="btn" type="button" data-do="intentBuilder.challenge">Start a challenge for this habit</button></div></form>';
  },on:{submit:function(e){
      if(e.target.id!=='intentForm')return;
      e.preventDefault();saveProfile({intent:readIntent()});toast('Intent saved.');
    }},
    actions:{challenge:function(){
      var it=readIntent();saveProfile({intent:it});
      state.prefill={name:it.habit||''};location.hash='challenges';
    }}
  });
  defineModule({id:'habitLoop',kicker:'Method',title:'The habit loop',span:5,render:function(){
    return '<ol class="loop">'+
      '<li><div><b>Cue</b><span>Make it obvious. Attach the habit to a time, a place or something you already do.</span></div></li>'+
      '<li><div><b>Craving</b><span>Make it attractive. Link it to the person you are becoming, not just the task.</span></div></li>'+
      '<li><div><b>Response</b><span>Make it easy. Shrink it to two minutes on the days you do not feel like it.</span></div></li>'+
      '<li><div><b>Reward</b><span>Make it satisfying. Tick the day and see the chain grow. That feeling is the reward.</span></div></li>'+
      '</ol><p class="meta">The loop of cue, craving, response and reward is the shared idea behind The Power of Habit and Atomic Habits.</p>';
  }});
})();
