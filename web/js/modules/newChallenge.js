'use strict';
/* Module: start a challenge (form). */
(function(){
  function formVals(){
    var r=document.querySelector('input[name="len"]:checked');
    var days=r?parseInt(r.value,10):21;
    var s=($('#cstart')&&$('#cstart').value)||today();
    if(s<today())s=today();
    return {days:days,start:s,name:(($('#cname')&&$('#cname').value)||'').trim()};
  }
  function previewText(days,start){
    return 'Day 1 is '+fShort(start)+'. Day '+days+' is '+fEnd(start,addDays(start,days-1))+'.';
  }
  function updatePreview(){
    var p=$('#preview');if(!p)return;
    var v=formVals();p.textContent=previewText(v.days,v.start);
  }
  function create(){
    var v=formVals();
    var c={id:'c'+Date.now().toString(36)+Math.random().toString(36).slice(2,6),
      name:v.name||(v.days+'-day challenge'),days:v.days,start:v.start,created:Date.now(),ticks:{},notes:{}};
    var end=addDays(c.start,c.days-1);
    state.prefill=null;
    persist(c);
    location.hash='c-'+c.id;
    toast('Challenge started: '+plural(c.days,'day')+', '+fShort(c.start)+' to '+fEnd(c.start,end)+'.');
  }
  defineModule({id:'newChallenge',kicker:'Begin',title:'Start a challenge',span:5,
    render:function(){
      var t=today(),pf=state.prefill||{};
      var lens=LENGTHS.map(function(n,i){
        return '<label class="len"><input type="radio" name="len" value="'+n+'"'+(i===0?' checked':'')+'><span><b>'+n+'</b><small>days</small></span></label>';
      }).join('');
      return '<form id="newForm" novalidate>'+
        '<div class="field"><label for="cname">What is it?</label><input type="text" id="cname" maxlength="60" placeholder="Morning run" autocomplete="off" value="'+esc(pf.name||'')+'"></div>'+
        '<fieldset><legend>How long?</legend><div class="lens">'+lens+'</div></fieldset>'+
        '<div class="field"><label for="cstart">First day</label><input type="date" id="cstart" value="'+t+'" min="'+t+'"></div>'+
        '<p class="preview" id="preview">'+esc(previewText(LENGTHS[0],t))+'</p>'+
        '<button class="btn primary" type="submit">Start challenge</button></form>';
    },
    on:{
      submit:function(e){if(e.target.id==='newForm'){e.preventDefault();create();}},
      input:function(e){if(e.target.id==='cstart')updatePreview();},
      change:function(e){if(e.target.id==='cstart'||e.target.name==='len')updatePreview();}
    }
  });
})();
