'use strict';
/* Pages. A page is a title plus a list of module ids. Order here is the nav order.
   To add a page: definePage({id,label,icon,title,sub,modules:[...]}). */
function greeting(){var h=new Date().getHours();return h<5?'Still up':(h<12?'Good morning':(h<17?'Good afternoon':'Good evening'));}

definePage({id:'home',label:'Home',icon:'home',
  eyebrow:function(){return fLong(today());},
  title:function(){var n=nameNow();return greeting()+(n?', '+n:'')+'.';},
  sub:function(){var a=analyze();return a.current>0?'Day '+a.current+' of your streak. Keep the chain.':'Show up today and start the chain.';},
  modules:['grit','today','glance','confidence','intentCard','review','counsel']});

definePage({id:'challenges',label:'Goals',icon:'target',
  eyebrow:'Streak tracker',title:'Habit challenges',sub:'Pick 21, 41, 90, 180 or 365 days. Tick each day on a real calendar and keep your streak.',
  modules:['newChallenge','challengeList']});

definePage({id:'habit',label:'Habit',icon:'spark',
  eyebrow:'Daily habit tracker',title:'Habit builder',sub:'One thing, done daily, aimed at the person you are becoming.',
  modules:['intentHero','intentBuilder','habitLoop']});

definePage({id:'insights',label:'Insights',icon:'chart',
  eyebrow:'Analysis',title:'Habit insights',sub:'Streaks, consistency and your grit score, measured.',
  modules:['glance','breakdown','weekday','heatmap','perf','review']});

definePage({id:'wisdom',label:'Wisdom',icon:'book',
  eyebrow:'Counsel',title:'Wisdom',sub:'Ideas from well-known books and the old scriptures, in our words.',
  modules:['library']});

definePage({id:'me',label:'Corner',icon:'user',header:false,modules:['diary']});

/* Reached from the avatar in the header, so it stays out of the main navigation. */
definePage({id:'account',label:'Account',icon:'user',nav:false,
  eyebrow:'Account',title:'Your account',sub:'Your photo, sign-in details and data. Only you can see them.',
  modules:['accountProfile','accountSecurity','backup','accountDanger']});
