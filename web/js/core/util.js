'use strict';
/* ---------- 2. state and utilities ---------- */
  var app=document.getElementById('app');
  var state={user:null,profile:{name:'',intent:{},avatar:{has:false,v:0}},allNotes:false,filter:'all',prefill:null,
    items:[],ready:false,view:'page',page:'home',cid:null,sel:null,drafts:{},confirmDel:false,stale:false};
  var backend=null;

  function $(s){return document.querySelector(s);}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function pad(n){return String(n).padStart(2,'0');}
  function keyOf(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
  function parseKey(k){var p=k.split('-').map(Number);return new Date(p[0],p[1]-1,p[2]);}
  function dayNo(k){var p=k.split('-').map(Number);return Date.UTC(p[0],p[1]-1,p[2])/864e5;}
  function addDays(k,n){var d=parseKey(k);d.setDate(d.getDate()+n);return keyOf(d);}
  function today(){return keyOf(new Date());}
  function fmt(k,o){return parseKey(k).toLocaleDateString('en-GB',o);}
  function fShort(k){return fmt(k,{weekday:'short',day:'numeric',month:'short'});}
  function fLong(k){return fmt(k,{weekday:'long',day:'numeric',month:'long'});}
  function fEnd(start,end){return parseKey(start).getFullYear()===parseKey(end).getFullYear()?fShort(end):fShort(end)+' '+parseKey(end).getFullYear();}
  function words(t){t=t.trim();return t?t.split(/\s+/):[];}
  function plural(n,w){return n+' '+w+(n===1?'':'s');}
  function clone(o){return JSON.parse(JSON.stringify(o));}
  function toast(msg){
    var t=$('#toast');t.textContent=msg;t.classList.add('show');
    clearTimeout(toast._t);toast._t=setTimeout(function(){t.classList.remove('show');},3400);
  }
