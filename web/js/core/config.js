'use strict';
/* ---------- 1. config and content ---------- */
  var BRAND='Habit Tracker';
  var LENGTHS=[21,41,90,180,365];
  var NOTE_MAX=30;
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DOW=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  var TIERS=[
    {min:0,name:'Spark',line:'The first proof is the hardest. Keep going.'},
    {min:100,name:'Builder',line:'A pattern is forming. Protect it.'},
    {min:250,name:'Steady',line:'You are becoming reliable to yourself.'},
    {min:400,name:'Confident Self',line:'You have the evidence. Walk like it.'},
    {min:650,name:'Relentless',line:'Setbacks pass through you.'},
    {min:850,name:'Unshakeable',line:'Discipline is who you are now.'}
  ];
  var CONFIDENT=3;

  /* Add an entry here and it appears in Wisdom and in Counsel of the day.
     Ideas are restated in our own words; src points to the original. */
  var WISDOM=[
    {kind:'book',tag:'Identity',src:'Atomic Habits',by:'James Clear',idea:'Lasting change starts with who you decide you are. Each small repetition is evidence for that identity.'},
    {kind:'book',tag:'Systems',src:'Atomic Habits',by:'James Clear',idea:'Goals set direction. Systems decide the outcome. Fall in love with the daily process and the result follows.'},
    {kind:'book',tag:'Start small',src:'Atomic Habits',by:'James Clear',idea:'Shrink a new habit until it takes two minutes. At the start, showing up matters more than size.'},
    {kind:'book',tag:'Perseverance',src:'Grit',by:'Angela Duckworth',idea:'Talent counts, but effort counts twice. It builds skill, then turns skill into achievement. Passion held over years separates finishers.'},
    {kind:'book',tag:'Direction',src:'Grit',by:'Angela Duckworth',idea:'Choose one top-level goal that gives the smaller goals meaning, and stay interested in it for a very long time.'},
    {kind:'book',tag:'Growth',src:'Mindset',by:'Carol Dweck',idea:'Treat ability as something you grow. Hearing "not yet" instead of "I cannot" keeps you in the game.'},
    {kind:'book',tag:'Vision',src:'The 7 Habits of Highly Effective People',by:'Stephen Covey',idea:'Begin with the end in mind. Picture who you want to be, then let that picture direct today’s choices.'},
    {kind:'book',tag:'Meaning',src:'Man’s Search for Meaning',by:'Viktor Frankl',idea:'When you know why you are doing something, you can endure almost any how. Meaning is the strongest fuel.'},
    {kind:'book',tag:'Habit loop',src:'The Power of Habit',by:'Charles Duhigg',idea:'Every habit runs on a loop of cue, routine and reward. Keep the cue and the reward, and change the routine.'},
    {kind:'book',tag:'Focus',src:'Deep Work',by:'Cal Newport',idea:'Protect long blocks of undistracted focus. The ability to concentrate is getting rarer and more valuable.'},
    {kind:'book',tag:'Limits',src:'Can’t Hurt Me',by:'David Goggins',idea:'When your mind says you are finished, you have often used only a fraction of what you have. Push past the first wall.'},
    {kind:'book',tag:'Obstacles',src:'The Obstacle Is the Way',by:'Ryan Holiday',idea:'What stands in the way becomes the way. Treat every obstacle as training material.'},
    {kind:'scripture',tag:'Practice',src:'Yoga Sutras 1.14',by:'Patanjali',orig:'sa tu dīrgha-kāla-nairāntarya-satkārāsevito dṛḍha-bhūmiḥ',idea:'Practice becomes firmly rooted when it is kept up for a long time, without breaks, and with real care.'},
    {kind:'scripture',tag:'Mind',src:'Yoga Sutras 1.2',by:'Patanjali',orig:'yogaś citta-vṛtti-nirodhaḥ',idea:'Yoga is the settling of the mind’s restless movements. Master attention and everything else gets easier.'},
    {kind:'scripture',tag:'Brahmacharya',src:'Yoga Sutras 2.38',by:'Patanjali',orig:'brahmacarya-pratiṣṭhāyāṁ vīrya-lābhaḥ',idea:'When restraint of sexual energy is firmly established, the text says, vitality and strength of will are gained. The tradition treats it as energy kept, not energy denied.'},
    {kind:'scripture',tag:'Brahmacharya',src:'Bhagavad Gita 17.14',by:'Vyasa',orig:'brahmacaryam ahiṁsā ca śārīraṁ tapa ucyate',idea:'The Gita lists brahmacharya among the disciplines of the body, beside purity, honesty and non-violence. Self-command begins in how you live in the body.'},
    {kind:'scripture',tag:'Brahmacharya',src:'Bhagavad Gita 6.14',by:'Vyasa',idea:'The steady practitioner is calm and fearless, firm in the vow of brahmacharya, with the mind under control and fixed on the goal.'},
    {kind:'scripture',tag:'Brahmacharya',src:'Bhagavad Gita 8.11',by:'Vyasa',idea:'The highest aim the sages praise is reached by those who live the disciplined life of brahmacharya, wanting nothing less.'},
    {kind:'scripture',tag:'Brahmacharya',src:'Chandogya Upanishad 8.5',by:'Upanishadic teachers',orig:'brahmacaryam eva tat',idea:'The Upanishad says that what people call sacrifice is really brahmacharya. A life of disciplined focus is itself the offering.'},
    {kind:'scripture',tag:'Effort',src:'Bhagavad Gita 2.47',by:'Vyasa',orig:'karmaṇy evādhikāras te mā phaleṣu kadācana',idea:'Your claim is on the work, never on its fruits. Give the effort completely and release the outcome.'},
    {kind:'scripture',tag:'Self-mastery',src:'Bhagavad Gita 6.5',by:'Vyasa',orig:'uddhared ātmanātmānaṁ nātmānam avasādayet',idea:'Lift yourself by your own effort and do not let yourself sink. The self can be your best friend or your worst enemy.'}
  ];

  var ICON={
    home:'<path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
    target:'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8"/>',
    spark:'<path d="M12 3l2.2 5.6L20 11l-5.8 2.4L12 19l-2.2-5.6L4 11l5.8-2.4z"/>',
    chart:'<path d="M4 20V4M4 20h16M8 16v-4M12 16V8M16 16v-6"/>',
    book:'<path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h10"/>',
    user:'<circle cx="12" cy="8" r="4"/><path d="M4 20c1-4 4-6 8-6s7 2 8 6"/>'
  };
  function icon(n){return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(ICON[n]||'')+'</svg>';}
  var CHECK='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3.2 3.2L13 4.8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var CAM='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h3l1.6-2.4h6.8L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="13" r="3.6" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>';

  