'use strict';
/* Sign in, create account, forgot password and reset password. The server owns every real check. */
(function(){
  var $=function(id){return document.getElementById(id);};
  var form=$('authForm'),err=$('err'),okEl=$('ok'),btn=$('submit'),mode='login',resetToken='';
  var EMAIL=/^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s.]{2,24}$/;
  var LABEL={login:'Sign in',register:'Create account',forgot:'Email me a reset link',reset:'Set new password'};
  var TITLE={login:'Welcome back.',register:'Start your chain.',forgot:'Reset your password.',reset:'Choose a new password.'};
  var SUB={login:'Pick up your streak where you left it.',register:'Create a free account. Your habits, notes and photo stay private to you.',
    forgot:'Enter your email and we will send you a link to choose a new password.',reset:'Pick something new. You will be signed out everywhere else.'};

  function setMode(m,focus,note){
    mode=m;var reg=m==='register';
    $('tab-login').setAttribute('aria-selected',String(m==='login'));$('tab-register').setAttribute('aria-selected',String(reg));
    document.querySelector('.auth-tabs').hidden=(m==='forgot'||m==='reset');
    $('auth-title').textContent=TITLE[m];$('auth-sub').textContent=SUB[m];
    $('f-name').hidden=!reg;$('f-email').hidden=(m==='reset');$('f-pass').hidden=(m==='forgot');
    $('pw-hint').hidden=!(reg||m==='reset');$('forgotLink').parentNode.hidden=(m!=='login');
    $('pw-label').textContent=m==='reset'?'New password':'Password';
    $('password').setAttribute('autocomplete',(reg||m==='reset')?'new-password':'current-password');
    btn.textContent=LABEL[m];
    $('switch').innerHTML=m==='register'?'Already have an account? <button type="button" id="goLogin">Sign in</button>':
      (m==='login'?'New here? <button type="button" id="goRegister">Create an account</button>':'<button type="button" id="goLogin">Back to sign in</button>');
    err.textContent='';okEl.textContent=note||'';
    if(history.replaceState)history.replaceState(null,'','#'+m);   /* a reset token never stays in the address bar */
    document.title=LABEL[m]+' | Habit Tracker';
    if(focus)(m==='reset'?$('password'):$('email')).focus();
  }
  function fromHash(){
    var h=location.hash,t=/^#reset=([\w-]{20,100})$/.exec(h);
    if(t){resetToken=t[1];setMode('reset');return;}
    setMode(h==='#register'?'register':(h==='#forgot'?'forgot':'login'));
  }
  function problem(){
    var email=$('email').value.trim(),pw=$('password').value;
    if(mode!=='reset'&&!EMAIL.test(email))return 'Enter a valid email address.';
    if(mode==='forgot')return '';
    if(!pw)return mode==='reset'?'Enter a new password.':'Enter your password.';
    if((mode==='register'||mode==='reset')&&pw.length<10)return 'Use at least 10 characters for your password.';
    return '';
  }
  function busy(on){btn.disabled=on;btn.textContent=on?'One moment...':LABEL[mode];}

  form.addEventListener('submit',function(e){
    e.preventDefault();
    var p=problem();if(p){err.textContent=p;return;}
    err.textContent='';okEl.textContent='';busy(true);
    var body={email:$('email').value.trim(),password:$('password').value};
    if(mode==='register')body.name=$('name').value.trim();
    if(mode==='forgot')body={email:body.email};
    if(mode==='reset')body={token:resetToken,new:$('password').value};
    fetch('/api/auth/'+mode,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Requested-With':'grit'},body:JSON.stringify(body)})
      .then(function(r){return r.json().catch(function(){return {};}).then(function(j){return {ok:r.ok,j:j};});})
      .then(function(res){
        busy(false);
        if(!res.ok){err.textContent=res.j.error||'Something went wrong. Please try again.';return;}
        if(mode==='forgot'){okEl.textContent=res.j.message||'Check your email for a reset link.';return;}
        if(mode==='reset'){$('password').value='';setMode('login',true,'Password updated. Sign in with your new password.');return;}
        try{localStorage.setItem('gritForgeIn','1');}catch(x){}
        location.replace('app.html');
      })
      .catch(function(){busy(false);err.textContent='Could not reach the server. Check your connection and try again.';});
  });
  $('tab-login').addEventListener('click',function(){setMode('login',true);});
  $('tab-register').addEventListener('click',function(){setMode('register',true);});
  $('forgotLink').addEventListener('click',function(){setMode('forgot',true);});
  $('switch').addEventListener('click',function(e){
    if(e.target.id==='goLogin')setMode('login',true);else if(e.target.id==='goRegister')setMode('register',true);
  });
  $('pwToggle').addEventListener('click',function(){
    var pw=$('password'),show=pw.type==='password';
    pw.type=show?'text':'password';this.textContent=show?'Hide':'Show';this.setAttribute('aria-pressed',String(show));
  });
  window.addEventListener('hashchange',fromHash);
  fromHash();

  /* Already signed in? Skip straight to the tracker (not while choosing a new password). */
  if(mode!=='reset')fetch('/api/auth/me',{credentials:'same-origin'}).then(function(r){if(r.ok){try{localStorage.setItem('gritForgeIn','1');}catch(x){}location.replace('app.html');}}).catch(function(){});
})();
