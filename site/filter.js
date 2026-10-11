const f=['q','ind','band','chk'].map(id=>document.getElementById(id));
function run(){const q=f[0].value.trim().toLowerCase();let n=0;
for(const li of document.querySelectorAll('#list li')){
const ok=(!q||li.dataset.name.includes(q))&&(!f[1].value||li.dataset.ind===f[1].value)&&(!f[2].value||li.dataset.band===f[2].value)&&(!f[3].value||li.dataset.checks.includes(' '+f[3].value+' '));
li.hidden=!ok;if(ok)n++}
document.getElementById('none').hidden=n>0;
document.getElementById('count').textContent=n===24?'Showing all 24 companies':'Showing '+n+' of 24 companies'}
f.forEach(e=>e.addEventListener('input',run));
