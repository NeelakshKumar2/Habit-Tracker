'use strict';
/* Talks to the Habit Tracker server. Every request carries the session cookie and our CSRF header.
   A 401 means the session ended, so we send the person to sign in. */
var Api={
  req:function(method,url,body,opts){
    opts=opts||{};
    var headers={'X-Requested-With':'grit'},init={method:method,headers:headers,credentials:'same-origin'};
    if(typeof FormData!=='undefined'&&body instanceof FormData){init.body=body;}
    else if(body!==undefined){headers['Content-Type']='application/json';init.body=JSON.stringify(body);}
    return fetch(url,init).then(function(r){
      if(r.status===401&&!opts.keepOn401)Api.expired();
      if(r.status===204)return null;
      return r.json().catch(function(){return {};}).then(function(j){
        if(!r.ok){var e=new Error((j&&j.error)||('Request failed ('+r.status+')'));e.status=r.status;throw e;}
        return j;
      });
    });
  },
  expired:function(){
    try{localStorage.removeItem('gritForgeIn');}catch(e){}
    location.replace('auth.html#login');
  }
};
