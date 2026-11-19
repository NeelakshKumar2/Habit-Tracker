'use strict';
/* Persistence. Everything lives on the server, scoped to the signed-in account. */
  var queues={};
  function enqueue(id,fn){
    var p=(queues[id]||Promise.resolve()).catch(function(){}).then(fn);
    queues[id]=p;return p;
  }
  function valid(c){return c&&typeof c.start==='string'&&typeof c.days==='number'&&c.days>0;}
  function sortItems(){state.items.sort(function(a,b){return (b.created||0)-(a.created||0);});}
  function cleanProfile(p){
    p=p||{};var a=p.avatar||{};
    return {name:p.name||'',intent:(p.intent&&typeof p.intent==='object')?p.intent:{},avatar:{has:!!a.has,v:a.v||0}};
  }
  function apiBackend(){
    return {
      kind:'api',
      start:function(){
        return Api.req('GET','/api/state').then(function(s){
          state.user=s.user;
          state.items=(s.challenges||[]).filter(valid);sortItems();
          state.profile=cleanProfile(s.profile);
          state.ready=true;refresh();
        }).catch(function(e){
          if(e.status===401)return;
          state.stale=true;renderPage();toast('Could not load your data. Check your connection and refresh.');
        });
      },
      save:function(c){var b=clone(c);delete b.id;return Api.req('PUT','/api/challenges/'+encodeURIComponent(c.id),b);},
      remove:function(id){return Api.req('DELETE','/api/challenges/'+encodeURIComponent(id));},
      saveProfile:function(p){return Api.req('PUT','/api/profile',{name:p.name,intent:p.intent});}
    };
  }
  function persist(c){
    var i=-1;for(var j=0;j<state.items.length;j++){if(state.items[j].id===c.id){i=j;break;}}
    if(i>=0)state.items[i]=c;else state.items.unshift(c);
    sortItems();refresh();
    return enqueue(c.id,function(){return backend.save(c);}).then(function(){return true;},function(e){
      toast((e&&e.message)||'Could not save that. Check your connection.');return false;
    });
  }
  function saveProfile(patch){
    state.profile=cleanProfile(Object.assign({},state.profile,patch));
    var p=clone(state.profile);
    updateNav();
    var cap=$('#cap');if(cap)cap.textContent=nameNow()||'me';
    refresh();
    return enqueue('profile',function(){return backend.saveProfile(p);}).catch(function(e){
      toast((e&&e.message)||'Could not save your profile. Check your connection.');
    });
  }
  function setFoot(){$('#foot').textContent=BRAND+'. Your data is private to your account.';}
  function nameNow(){return (state.profile.name||'').trim()||'';}
  function hasAvatar(){return !!(state.profile.avatar&&state.profile.avatar.has);}
  function avatarUrl(){return '/api/me/avatar?v='+encodeURIComponent(state.profile.avatar.v||0);}
  function initial(){var s=nameNow()||(state.user&&state.user.email)||'?';return s.charAt(0).toUpperCase();}
  function avatarHTML(cls){
    return hasAvatar()?'<img class="av '+cls+'" alt="" src="'+esc(avatarUrl())+'">':'<span class="av ini '+cls+'" aria-hidden="true">'+esc(initial())+'</span>';
  }
