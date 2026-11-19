'use strict';
/* Module: wisdom library with filters. Add entries in js/core/config.js. */
defineModule({id:'library',kicker:'Library',title:'Counsel',span:12,render:function(){
  var F=[['all','All'],['book','Books'],['scripture','Scripture'],['brahma','Brahmacharya']];
  var f=state.filter;
  var list=WISDOM.filter(function(w){return f==='all'||(f==='brahma'?w.tag==='Brahmacharya':w.kind===f);});
  var chips='<div class="chips" role="group" aria-label="Filter">'+F.map(function(x){
    return '<button type="button" class="fchip" data-do="library.filter" data-f="'+x[0]+'" aria-pressed="'+(f===x[0])+'">'+x[1]+'</button>';
  }).join('')+'</div>';
  var cards='<div class="wgrid">'+list.map(function(w){
    return '<article class="wcard"><div class="wtop"><span class="chip">'+(w.kind==='book'?'Book':'Scripture')+'</span><span class="wtag">'+esc(w.tag)+'</span></div>'+
      '<p class="widea">'+esc(w.idea)+'</p>'+(w.orig?'<p class="worig" lang="sa">'+esc(w.orig)+'</p>':'')+
      '<p class="wsrc">'+esc(w.src)+' · '+esc(w.by)+'</p></article>';
  }).join('')+'</div>';
  return chips+cards+'<p class="meta">Ideas are restated in our own words. Each source is named so you can read the original.</p>';
},actions:{filter:function(b){state.filter=b.getAttribute('data-f');refresh();}}});
