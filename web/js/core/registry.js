'use strict';
/* ---------- 4. module system ---------- */
  var MODULES={},PAGES=[];
  function defineModule(m){MODULES[m.id]=m;}
  function definePage(p){PAGES.push(p);}
  function pageById(id){for(var i=0;i<PAGES.length;i++){if(PAGES[i].id===id)return PAGES[i];}return null;}
  function modHTML(id){
    var m=MODULES[id];if(!m)return '';
    var head=m.title?'<header class="mh">'+(m.kicker?'<p class="kick">'+esc(m.kicker)+'</p>':'')+'<h2>'+esc(m.title)+'</h2></header>':'';
    return '<section class="mod span-'+(m.span||12)+(m.bare?' bare':'')+'" data-mod="'+esc(id)+'">'+head+m.render()+'</section>';
  }
  function liveRows(){
    var rows=[];
    state.items.forEach(function(c){var s=stats(c);if(s.t>=0&&s.t<c.days)rows.push({c:c,s:s});});
    return rows;
  }
