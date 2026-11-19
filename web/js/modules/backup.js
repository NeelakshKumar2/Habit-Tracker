'use strict';
/* Module: export and import all your data as one JSON file. */
(function(){
  function exportData(){
    var blob=new Blob([JSON.stringify({app:'grit',version:2,exported:new Date().toISOString(),profile:{name:state.profile.name,intent:state.profile.intent},challenges:state.items},null,2)],{type:'application/json'});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='grit-backup-'+today()+'.json';
    document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(a.href);},1000);
    toast('Backup downloaded.');
  }
  function importData(file){
    var fr=new FileReader();
    fr.onerror=function(){toast('That file could not be read.');};
    fr.onload=function(){
      var d;try{d=JSON.parse(fr.result);}catch(e){toast('That is not a Grit backup file.');return;}
      var list=(d&&d.app==='grit'&&Array.isArray(d.challenges))?d.challenges.filter(valid):null;
      if(!list){toast('That is not a Grit backup file.');return;}
      list.forEach(function(c,i){c.id=c.id||('c'+Date.now().toString(36)+i);c.ticks=c.ticks||{};c.notes=c.notes||{};c.created=c.created||Date.now();persist(c);});
      if(d.profile)saveProfile({name:d.profile.name,intent:d.profile.intent});
      toast('Imported '+plural(list.length,'challenge')+'.');
    };
    fr.readAsText(file);
  }
  defineModule({id:'backup',kicker:'Your data',title:'Backup',span:12,render:function(){
    return '<p class="muted">Download a copy of your challenges, notes and profile, or restore one. You can also bring in a backup from an older version of Grit.</p>'+
      '<div class="row"><button type="button" class="btn" data-do="backup.export">Export backup</button>'+
      '<input class="vh" type="file" id="importfile" accept="application/json,.json"><label class="btn photobtn" for="importfile">Import backup</label></div>';
  },actions:{export:exportData},on:{change:function(e){
    var t=e.target;if(t.id==='importfile'&&t.files&&t.files[0]){importData(t.files[0]);t.value='';}
  }}});
})();
