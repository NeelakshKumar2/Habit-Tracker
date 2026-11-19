'use strict';
/* ---------- 3. domain ---------- */
  function stats(c){
    var t=dayNo(today())-dayNo(c.start);
    var done=0;for(var k in (c.ticks||{})){if(c.ticks[k])done++;}
    return {t:t,done:done,end:addDays(c.start,c.days-1),complete:done>=c.days,ended:t>=c.days,notStarted:t<0};
  }
  function statusOf(c){
    var s=stats(c);
    if(s.complete)return {cls:'done',label:'Completed'};
    if(s.notStarted)return {cls:'',label:'Starts '+fShort(c.start)};
    if(s.ended)return {cls:'ended',label:'Ended'};
    return {cls:'live',label:'Day '+(s.t+1)+' of '+c.days};
  }
  function tierIdx(score){var t=0;TIERS.forEach(function(x,i){if(score>=x.min)t=i;});return t;}

  /* Grit score, 0 to 1000.
     Points: 3 per day kept, 1.5 per day of each finished challenge, 2 per day of the longest streak, 2 per note.
     Those points are scaled by consistency (kept days against days that have passed, worth 50 to 100 percent)
     and recency (a small drop after a week without a tick). The curve flattens near 1000, so it takes
     real, repeated effort to climb: about a finished 90-day challenge with notes reaches Confident Self. */
  function analyze(){
    var tk=today(),tkNo=dayNo(tk);
    var ticked={},A={ticks:0,elapsed:0,notes:0,words:0,completed:0,active:0,upcoming:0,bonus:0};
    state.items.forEach(function(c){
      var s=stats(c);A.ticks+=s.done;
      A.elapsed+=Math.max(0,Math.min(c.days,s.t+1));
      for(var i in c.ticks){if(c.ticks[i]){var k=addDays(c.start,+i);ticked[k]=(ticked[k]||0)+1;}}
      for(var n in c.notes){if(c.notes[n]){A.notes++;A.words+=words(c.notes[n]).length;}}
      if(s.complete){A.completed++;A.bonus+=c.days*1.5;}
      else if(s.notStarted)A.upcoming++;
      else if(!s.ended)A.active++;
    });
    var keys=Object.keys(ticked).sort(),longest=0,run=0,prev=null;
    keys.forEach(function(k){run=(prev!==null&&dayNo(k)-dayNo(prev)===1)?run+1:1;if(run>longest)longest=run;prev=k;});
    var cursor=ticked[tk]?tk:addDays(tk,-1),current=0;
    while(ticked[cursor]){current++;cursor=addDays(cursor,-1);}
    var last=keys.length?keys[keys.length-1]:null;
    var idle=last?Math.max(0,tkNo-dayNo(last)):0;
    var rate=A.elapsed?Math.min(1,A.ticks/A.elapsed):0;
    var cons=A.elapsed?0.5+0.5*rate:1;
    var rec=last?1-Math.min(0.15,Math.max(0,idle-7)*0.01):1;
    var pts={show:A.ticks*3,finish:Math.round(A.bonus),streak:longest*2,reflect:A.notes*2};
    var raw=pts.show+pts.finish+pts.streak+pts.reflect;
    var score=Math.round(1000*(1-Math.exp(-raw*cons*rec/1200)));
    var ti=tierIdx(score),nx=TIERS[ti+1]||null;
    var pct=nx?(score-TIERS[ti].min)/(nx.min-TIERS[ti].min):1;
    return {A:A,ticked:ticked,longest:longest,current:current,idle:idle,rate:rate,cons:cons,rec:rec,pts:pts,raw:raw,
      score:score,tier:ti,next:nx,pct:Math.max(0,Math.min(1,pct)),daysKept:keys.length};
  }

  