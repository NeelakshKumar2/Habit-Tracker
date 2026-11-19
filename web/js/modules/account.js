'use strict';
/* Account page modules: profile photo and name, sign-in security, and permanent deletion. */
(function(){
  var MAX_BYTES=2*1024*1024;

  /* Phones save big photos. Crop to a square and shrink here so uploads stay small and quick. */
  function shrink(file){
    return new Promise(function(done){
      if(!window.createImageBitmap){done(file);return;}
      createImageBitmap(file).then(function(bmp){
        var S=512,m=Math.min(bmp.width,bmp.height),cv=document.createElement('canvas');cv.width=S;cv.height=S;
        cv.getContext('2d').drawImage(bmp,(bmp.width-m)/2,(bmp.height-m)/2,m,m,0,0,S,S);
        cv.toBlob(function(b){done(b||file);},'image/jpeg',0.88);
      }).catch(function(){done(file);});
    });
  }
  function uploadPhoto(file){
    if(!file)return;
    if(!/^image\//.test(file.type)){toast('Choose an image file.');return;}
    toast('Uploading...');
    shrink(file).then(function(blob){
      if(blob.size>MAX_BYTES){throw new Error('That image is over 2 MB. Choose a smaller one.');}
      var fd=new FormData();fd.append('file',blob,'avatar.jpg');
      return Api.req('PUT','/api/me/avatar',fd);
    }).then(function(r){
      state.profile.avatar={has:true,v:r.avatar.v};updateNav();refresh();toast('Photo updated.');
    }).catch(function(e){toast(e.message||'That photo could not be uploaded.');});
  }
  function since(){
    var t=state.user&&state.user.created_at;if(!t)return '';
    return new Date(t*1000).toLocaleDateString('en-GB',{month:'long',year:'numeric'});
  }
  function leave(){
    try{localStorage.removeItem('gritForgeIn');}catch(e){}
    location.replace('auth.html#login');
  }

  defineModule({id:'accountProfile',kicker:'Profile',title:'Photo and name',span:12,
    render:function(){
      var u=state.user||{},has=hasAvatar();
      return '<div class="acct-head"><div class="acct-av">'+avatarHTML('big')+'</div><div class="acct-meta">'+
        '<p class="acct-name">'+esc(nameNow()||'Add your name')+'</p><p class="muted">'+esc(u.email||'')+'</p>'+
        (since()?'<p class="meta">Member since '+esc(since())+'</p>':'')+
        '<div class="row"><input class="vh" type="file" id="avatarfile" accept="image/png,image/jpeg,image/webp,image/gif">'+
        '<label class="btn photobtn" for="avatarfile">'+(has?'Change photo':'Add photo')+'</label>'+
        (has?'<button type="button" class="btn ghost" data-do="accountProfile.rmPhoto">Remove photo</button>':'')+'</div>'+
        '<p class="meta">JPG, PNG, WebP or GIF, up to 2 MB. Cropped to a square.</p></div></div>'+
        '<form id="nameForm" class="acct-form" novalidate><div class="field"><label for="acct-name">Display name</label>'+
        '<input type="text" id="acct-name" maxlength="30" autocomplete="name" value="'+esc(state.profile.name||'')+'"></div>'+
        '<button class="btn primary" type="submit">Save name</button></form>';
    },
    on:{
      change:function(e){var t=e.target;if(t.id==='avatarfile'&&t.files&&t.files[0]){uploadPhoto(t.files[0]);t.value='';}},
      submit:function(e){
        if(e.target.id!=='nameForm')return;e.preventDefault();
        saveProfile({name:($('#acct-name').value||'').trim().slice(0,30)});toast('Name saved.');
      }
    },
    actions:{rmPhoto:function(){
      Api.req('DELETE','/api/me/avatar').then(function(r){state.profile.avatar=r.avatar;updateNav();refresh();toast('Photo removed.');})
        .catch(function(e){toast(e.message);});
    }}
  });

  defineModule({id:'accountSecurity',kicker:'Security',title:'Password and sessions',span:12,
    render:function(){
      return '<form id="pwForm" class="acct-form" novalidate>'+
        '<div class="field"><label for="pw-cur">Current password</label><input type="password" id="pw-cur" maxlength="128" autocomplete="current-password"></div>'+
        '<div class="field"><label for="pw-new">New password</label><input type="password" id="pw-new" maxlength="128" autocomplete="new-password" aria-describedby="pw-help"></div>'+
        '<p class="meta" id="pw-help">At least 10 characters. Changing it signs you out on your other devices.</p>'+
        '<p class="err" id="pw-err" role="alert" aria-live="assertive"></p>'+
        '<button class="btn primary" type="submit">Change password</button></form>'+
        '<div class="row sess"><button type="button" class="btn" data-do="accountSecurity.out">Sign out</button>'+
        '<button type="button" class="btn ghost" data-do="accountSecurity.outAll">Sign out of all devices</button></div>';
    },
    on:{submit:function(e){
      if(e.target.id!=='pwForm')return;e.preventDefault();
      var cur=$('#pw-cur').value,nw=$('#pw-new').value,err=$('#pw-err');err.textContent='';
      if(!cur||nw.length<10){err.textContent=!cur?'Enter your current password.':'Use at least 10 characters for the new password.';return;}
      Api.req('POST','/api/auth/change-password',{current:cur,new:nw},{keepOn401:false}).then(function(){
        $('#pw-cur').value='';$('#pw-new').value='';toast('Password changed.');
      }).catch(function(x){err.textContent=x.message;});
    }},
    actions:{
      out:function(){Api.req('POST','/api/auth/logout',undefined,{keepOn401:true}).then(leave,leave);},
      outAll:function(){Api.req('POST','/api/auth/logout-all',undefined,{keepOn401:true}).then(leave,leave);}
    }
  });

  var ask=false;
  defineModule({id:'accountDanger',kicker:'Danger zone',title:'Delete account',span:12,
    render:function(){
      if(!ask){
        return '<p class="muted">Permanently delete your account and everything in it: challenges, notes, diary pages, photo and sign-in. This cannot be undone. Download a backup first if you want a copy.</p>'+
          '<div class="row"><button type="button" class="btn danger" data-do="accountDanger.open">Delete my account</button></div>';
      }
      return '<form id="delForm" class="acct-form" novalidate><p class="muted">This is permanent. Enter your password and type <b>DELETE</b> to confirm.</p>'+
        '<div class="field"><label for="del-pw">Your password</label><input type="password" id="del-pw" maxlength="128" autocomplete="current-password"></div>'+
        '<div class="field"><label for="del-ok">Type DELETE</label><input type="text" id="del-ok" maxlength="6" autocomplete="off" autocapitalize="characters" spellcheck="false"></div>'+
        '<p class="err" id="del-err" role="alert" aria-live="assertive"></p>'+
        '<div class="row"><button class="btn danger" id="del-go" type="submit" disabled>Permanently delete account</button>'+
        '<button class="btn ghost" type="button" data-do="accountDanger.cancel">Cancel</button></div></form>';
    },
    on:{
      input:function(e){
        if(e.target.id!=='del-pw'&&e.target.id!=='del-ok')return;
        $('#del-go').disabled=!($('#del-pw').value&&$('#del-ok').value.trim()==='DELETE');
      },
      submit:function(e){
        if(e.target.id!=='delForm')return;e.preventDefault();
        var go=$('#del-go'),err=$('#del-err');go.disabled=true;err.textContent='';
        Api.req('DELETE','/api/account',{password:$('#del-pw').value},{keepOn401:true}).then(function(){
          try{localStorage.removeItem('gritForgeIn');}catch(x){}
          location.replace('./?landing=1&deleted=1');
        }).catch(function(x){err.textContent=x.message;go.disabled=false;});
      }
    },
    actions:{open:function(){ask=true;refresh();var f=$('#del-pw');if(f)f.focus();},cancel:function(){ask=false;refresh();}}
  });
})();
