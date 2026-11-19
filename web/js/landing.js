'use strict';
/* Landing page helpers. Signed-in visitors go straight to their tracker; search engines and new visitors see the page. */
try{
  var q=location.search;
  if(q.indexOf('deleted=1')>=0){var n=document.getElementById('deleted-note');if(n)n.hidden=false;try{localStorage.removeItem('gritForgeIn');}catch(e){}}
  else if(localStorage.getItem('gritForgeIn')&&q.indexOf('landing')<0)location.replace('app.html');
}catch(e){}
