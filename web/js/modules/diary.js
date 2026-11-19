'use strict';
/* Module: My Corner, the diary page (name, stamps, daily notes). The photo is managed on the Account page. */
(function(){
  defineModule({id:'diary',span:12,bare:true,render:function(){
    var a=analyze(),done=[],active=0,ticks=0,notes=0,entries=[];
    state.items.forEach(function(c){
      var s=stats(c);ticks+=s.done;
      for(var k in c.notes){if(c.notes[k]){notes++;entries.push({c:c,i:+k,t:c.notes[k],d:addDays(c.start,+k)});}}
      if(s.complete)done.push(c);else if(!s.ended&&!s.notStarted)active++;
    });
    done.sort(function(x,y){return dayNo(y.start)-dayNo(x.start);});
    entries.sort(function(x,y){return x.d<y.d?1:(x.d>y.d?-1:0);});
    var n=done.length;
    var msg=n===0?(state.items.length?'Finish every day of a challenge and it gets stamped here.':'Start a challenge and finish every day to get your first stamp.')
      :(n===1?'One challenge finished. Start another and keep going.':n+' challenges finished. Every single day ticked.');
    var ph=hasAvatar();
    var pic=ph?'<img class="photo" alt="Your photo" src="'+esc(avatarUrl())+'">':'<a class="ph" href="#account">'+CAM+'<span>Add photo</span></a>';
    var cover='<div class="cover"><div class="polaroid">'+pic+'<span class="cap" id="cap">'+esc(nameNow()||'me')+'</span></div>'+
      '<div class="who"><h1 class="title">My Corner</h1><p class="belongs">This diary belongs to</p>'+
      '<input class="nameinput" id="pname" type="text" maxlength="30" aria-label="Your name" autocomplete="off" placeholder="Write your name" value="'+esc(state.profile.name||'')+'">'+
      '<div class="row"><a class="btn" href="#account">'+(ph?'Change photo':'Add photo')+'</a></div></div></div>';
    var tally='<div><div class="bigrow"><b>'+n+'</b><span>'+(n===1?'challenge':'challenges')+' completed</span></div>'+
      '<svg class="scribble" viewBox="0 0 260 14" preserveAspectRatio="none" aria-hidden="true"><path d="M2 9C30 2 60 13 95 7S160 2 190 8 240 12 258 5" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></svg>'+
      '<p class="note-msg">'+esc(msg)+'</p><p class="gritline">Grit<b>'+a.score+'</b>'+esc(TIERS[a.tier].name)+'</p></div>'+
      '<div class="stickies"><div class="sticky"><b>'+active+'</b><span>in progress</span></div><div class="sticky"><b>'+ticks+'</b><span>days ticked</span></div><div class="sticky"><b>'+notes+'</b><span>notes written</span></div></div>';
    var stamps=n?'<div class="stamps">'+done.map(function(c){
      var end=addDays(c.start,c.days-1);
      return '<a class="stamp" href="#c-'+esc(c.id)+'">'+CHECK+'<span class="sn">'+esc(c.name)+'</span><span class="sd">'+c.days+' days</span><span class="sx">'+esc(fmt(end,{day:'numeric',month:'short',year:'numeric'}))+'</span></a>';
    }).join('')+'</div>':'<p class="note-msg">No stamps yet. Every finished challenge lands here.</p>';
    var shown=state.allNotes?entries:entries.slice(0,8);
    var pages=entries.length?'<div class="pages">'+shown.map(function(e){
      return '<a class="entry" href="#c-'+esc(e.c.id)+'"><div class="edate"><b>'+esc(fShort(e.d))+'</b><small>'+esc(e.c.name)+' · day '+(e.i+1)+'</small></div><p class="etext">'+esc(e.t)+'</p></a>';
    }).join('')+(entries.length>8?'<button class="btn ghost morebtn" type="button" data-do="diary.more">'+(state.allNotes?'Show fewer pages':'Show all '+entries.length+' pages')+'</button>':'')+'</div>'
      :'<p class="note-msg">Your daily notes get written on these pages.</p>';
    return '<div class="sheet">'+cover+tally+'<section><h2 class="h-hand">Stamps collected</h2>'+stamps+'</section><section><h2 class="h-hand">Pages from my diary</h2>'+pages+'</section></div>';
  },
  on:{change:function(e){
    var t=e.target;
    if(t.id==='pname'){saveProfile({name:t.value.trim().slice(0,30)});}
  }},
  actions:{more:function(){state.allNotes=!state.allNotes;refresh();}}});
})();
