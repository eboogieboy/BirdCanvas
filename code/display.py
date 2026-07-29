from pathlib import Path

from artwork_store import migrate_legacy_artwork
from gallery_library import build_library
from paths import OUTPUT_DIR


def build_display_page() -> None:
    migrate_legacy_artwork()
    build_library()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(DISPLAY_HTML, encoding="utf-8")
    control_dir = OUTPUT_DIR / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    (control_dir / "index.html").write_text(CONTROL_HTML, encoding="utf-8")
    print("✓ Dumb display page saved to output/index.html")
    print("✓ Phone control page saved to output/control/index.html")
    print("✓ Gallery library remains at output/gallery/index.html")


DISPLAY_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GalleryOS</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}
body{position:relative}
.artwork-layer{position:absolute;inset:0;z-index:1;width:100%;height:100%;object-fit:contain;opacity:0;transition:opacity 1.1s cubic-bezier(.4,0,.2,1);will-change:opacity;backface-visibility:hidden}
.artwork-layer.visible{opacity:1}
#message{position:absolute;inset:0;display:grid;place-items:center;color:#aaa;font-family:Arial,sans-serif;text-align:center;padding:24px}
#reveal{position:absolute;inset:0;z-index:5;display:flex;align-items:center;justify-content:center;background:rgba(5,5,5,.985);color:#f5f1e8;font-family:Arial,sans-serif;text-align:center;opacity:0;pointer-events:none;transition:opacity 1.1s cubic-bezier(.4,0,.2,1),background-color 1.25s ease}
#reveal.visible{opacity:1}
#reveal.receding{background:rgba(5,5,5,0)}
#reveal.compact .reveal-inner{max-width:min(74vw,820px)}
#reveal.compact .reveal-kicker{margin-bottom:20px}
#reveal.compact .reveal-title{font-size:clamp(34px,4.7vw,72px)}
#reveal.compact .reveal-date,#reveal.compact .reveal-collection,#reveal.compact .reveal-birds{display:none}
.reveal-inner{max-width:min(80vw,980px);padding:56px;opacity:0;transform:translateY(12px);transition:opacity .9s ease,transform 1.15s cubic-bezier(.22,1,.36,1)}
#reveal.visible .reveal-inner{opacity:1;transform:translateY(0)}
#reveal.receding .reveal-inner{opacity:0;transform:translateY(-8px)}
.reveal-kicker{font-size:clamp(12px,1.25vw,19px);font-weight:600;letter-spacing:.36em;text-transform:uppercase;opacity:.62;margin-bottom:30px}
.reveal-title{font-family:Georgia,'Times New Roman',serif;font-size:clamp(38px,5.5vw,88px);font-weight:400;line-height:1.04;letter-spacing:-.018em;margin:0}
.reveal-date{font-size:clamp(15px,1.75vw,27px);margin-top:26px;opacity:.72}
.reveal-collection{font-family:Georgia,'Times New Roman',serif;font-size:clamp(15px,1.55vw,23px);font-style:italic;margin-top:13px;letter-spacing:.025em;opacity:.58}
.reveal-birds{max-width:800px;margin:32px auto 0;font-size:clamp(14px,1.5vw,23px);line-height:1.65;letter-spacing:.025em;opacity:.78}
.reveal-birds:empty{display:none}
#sleep-cover{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .7s ease;z-index:10}body.screen-off #sleep-cover{opacity:1}
</style>
</head>
<body>
<img id="layer-a" class="artwork-layer" alt="">
<img id="layer-b" class="artwork-layer" alt="">
<div id="message">Loading GalleryOS…</div><div id="reveal"><div class="reveal-inner"><div id="reveal-kicker" class="reveal-kicker">Now Exhibiting</div><h1 id="reveal-title" class="reveal-title"></h1><div id="reveal-date" class="reveal-date"></div><div id="reveal-collection" class="reveal-collection"></div><div id="reveal-birds" class="reveal-birds"></div></div></div><div id="sleep-cover"></div>
<script>
const layers=[document.querySelector('#layer-a'),document.querySelector('#layer-b')];
const message=document.querySelector('#message');
const reveal=document.querySelector('#reveal');
const revealKicker=document.querySelector('#reveal-kicker');
const revealTitle=document.querySelector('#reveal-title');
const revealDate=document.querySelector('#reveal-date');
const revealCollection=document.querySelector('#reveal-collection');
const revealBirds=document.querySelector('#reveal-birds');
let visibleIndex=0;
let displayedKey=null;
let switching=false;
let pollTimer=null;
let consecutiveFailures=0;
let lastStatus=null;

function artworkKey(artwork){
  return `${artwork.id}|${artwork.image_url}|${artwork.display_revision||''}`;
}

function imageUrl(artwork){
  const separator=artwork.image_url.includes('?')?'&':'?';
  return `${artwork.image_url}${separator}v=${encodeURIComponent(artwork.display_revision||Date.now())}`;
}

function revealDateLabel(artwork){
  const value=artwork.observation_date||artwork.created_at;
  if(!value)return '';
  const date=new Date(`${String(value).slice(0,10)}T12:00:00`);
  return Number.isNaN(date.getTime())?'':date.toLocaleDateString([], {day:'numeric',month:'long',year:'numeric'});
}

function prepareReveal(artwork){
  const exhibition=artwork.exhibition||{};
  const isBirdCanvas=artwork.collection==='birdcanvas';
  reveal.classList.toggle('compact',!isBirdCanvas);
  revealKicker.textContent=isBirdCanvas?'Now Exhibiting':'Now Showing';
  revealTitle.textContent=artwork.title||'GalleryOS';
  revealDate.textContent=revealDateLabel(artwork);
  revealCollection.textContent=exhibition.collection||artwork.creative_collection||(isBirdCanvas?'BirdCanvas Collection':'GalleryOS Collection');
  const birds=Array.isArray(artwork.species)?artwork.species.filter(Boolean):[];
  revealBirds.textContent=isBirdCanvas&&birds.length?birds.join(' · '):'';
  return {isBirdCanvas};
}

async function switchArtwork(artwork){
  const key=artworkKey(artwork);
  if(key===displayedKey||switching)return;

  switching=true;
  const nextIndex=1-visibleIndex;
  const nextLayer=layers[nextIndex];
  const currentLayer=layers[visibleIndex];
  const preload=new Image();
  const settings=(lastStatus&&lastStatus.display_settings)||{};
  const duration=Math.max(0,Number(settings.transition_seconds??1.1));
  const transition=settings.transition||'fade';

  nextLayer.style.transitionDuration=`${duration}s`;
  currentLayer.style.transitionDuration=`${duration}s`;

  const timeout=window.setTimeout(()=>{
    preload.src='';
    switching=false;
    consecutiveFailures+=1;
    console.error('Artwork load timed out:',artwork.image_url);
  },20000);

  preload.onload=()=>{
    window.clearTimeout(timeout);
    nextLayer.src=preload.src;
    nextLayer.alt=artwork.title||'GalleryOS artwork';

    requestAnimationFrame(()=>{
      message.style.display='none';

      const finish=()=>{
        reveal.classList.remove('visible','receding');
        currentLayer.classList.remove('visible');
        currentLayer.removeAttribute('src');
        visibleIndex=nextIndex;
        displayedKey=key;
        document.title=artwork.title||'GalleryOS';
        switching=false;
        consecutiveFailures=0;
      };

      if(transition==='cut'||duration===0){
        currentLayer.classList.remove('visible');
        nextLayer.classList.add('visible');
        finish();
        return;
      }

      const revealMode=prepareReveal(artwork);
      const revealDuration=revealMode.isBirdCanvas?duration:Math.min(duration,.65);
      reveal.style.transitionDuration=`${revealDuration}s`;
      currentLayer.classList.remove('visible');
      reveal.classList.add('visible');

      const revealHold=revealMode.isBirdCanvas?3000:1100;
      window.setTimeout(()=>{
        nextLayer.classList.add('visible');
        reveal.classList.add('receding');
        const dissolveMs=revealMode.isBirdCanvas?Math.max(1250,Math.ceil(duration*1000)+120):Math.max(700,Math.ceil(revealDuration*1000)+80);
        window.setTimeout(finish,dissolveMs);
      },Math.ceil(duration*1000)+revealHold);
    });
  };

  preload.onerror=()=>{
    window.clearTimeout(timeout);
    console.error('Artwork could not be loaded:',artwork.image_url);
    consecutiveFailures+=1;
    switching=false;
  };

  preload.decoding='async';
  preload.src=imageUrl(artwork);
}

function applyDisplaySettings(status){
  const settings=status.display_settings||{};
  lastStatus=status;
  document.body.classList.toggle('screen-off',status.screen_on===false);

  const backgrounds={
    black:'#000000',
    soft_black:'#101010',
    white:'#ffffff'
  };
  document.documentElement.style.background=backgrounds[settings.background]||'#000000';
  document.body.style.background=backgrounds[settings.background]||'#000000';

  const fit=settings.fit_mode||'contain';
  const rotation=Number(settings.rotation||0);
  const duration=Math.max(0,Number(settings.transition_seconds??1.1));

  for(const layer of layers){
    layer.style.objectFit=fit;
    layer.style.transitionDuration=`${duration}s`;

    if(rotation===90){
      layer.style.inset='auto';layer.style.left='50%';layer.style.top='50%';
      layer.style.width='100vh';layer.style.height='100vw';
      layer.style.transform='translate(-50%,-50%) rotate(90deg)';
    }else if(rotation===270){
      layer.style.inset='auto';layer.style.left='50%';layer.style.top='50%';
      layer.style.width='100vh';layer.style.height='100vw';
      layer.style.transform='translate(-50%,-50%) rotate(-90deg)';
    }else{
      layer.style.inset='0';layer.style.left='';layer.style.top='';
      layer.style.width='100%';layer.style.height='100%';layer.style.transform='none';
    }
  }

  const pollSeconds=Math.max(2,Number(settings.poll_seconds||5));
  scheduleNextPoll(pollSeconds*1000);
}

function scheduleNextPoll(delay){
  if(pollTimer)window.clearTimeout(pollTimer);
  pollTimer=window.setTimeout(refreshDisplay,delay);
}

async function refreshDisplay(){
  try{
    const response=await fetch('/api/display',{cache:'no-store'});
    if(!response.ok)throw new Error('Status request failed');
    const status=await response.json();
    applyDisplaySettings(status);
    const artwork=status.artwork;
    if(!artwork){
      if(!displayedKey){
        message.style.display='grid';
        message.textContent='No artwork is available.';
      }
      return;
    }
    await switchArtwork(artwork);
  }catch(error){
    console.error(error);
    consecutiveFailures+=1;
    const delay=Math.min(30000,5000*Math.max(1,consecutiveFailures));
    scheduleNextPoll(delay);
  }
}

document.addEventListener('visibilitychange',()=>{
  if(!document.hidden)refreshDisplay();
});
window.addEventListener('online',refreshDisplay);
refreshDisplay();
</script>
</body>
</html>'''


CONTROL_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#f2efe8">
<title>Gallery</title>
<style>
:root{--paper:#f2efe8;--card:#fbfaf7;--ink:#1e2522;--muted:#6e746f;--line:#ddd8cf;--accent:#344b43;--soft:#e5e9e4;--danger:#8b3d3d;--shadow:0 12px 34px rgba(33,38,35,.09);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink)}button,input,select{font:inherit}button{cursor:pointer}.hidden{display:none!important}.app{width:min(820px,100%);margin:0 auto;padding:env(safe-area-inset-top) 18px calc(96px + env(safe-area-inset-bottom))}.topbar{display:flex;align-items:center;justify-content:space-between;padding:22px 2px 14px}.brand{font:700 28px/1 Georgia,serif}.version{font-size:12px;color:var(--muted)}.panel{display:none}.panel.active{display:block}.card{background:var(--card);border:1px solid var(--line);border-radius:24px;box-shadow:var(--shadow);overflow:hidden}.hero{position:relative;min-height:420px;background:#202522}.hero img{width:100%;height:420px;object-fit:cover;display:block}.hero-gradient{position:absolute;inset:35% 0 0;background:linear-gradient(transparent,rgba(8,12,10,.82))}.hero-label{position:absolute;left:22px;right:22px;bottom:22px;color:#fff}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:11px;font-weight:800}.hero h1{margin:7px 0 4px;font:700 34px/1.05 Georgia,serif}.hero p{margin:0;color:rgba(255,255,255,.78)}.hero-empty{min-height:300px;display:grid;place-items:center;color:#bfc4c0}.section{margin-top:18px}.section h2{font:700 22px/1.1 Georgia,serif;margin:0 0 12px}.mode-row,.quick-grid,.stats{display:grid;gap:12px}.mode-row{grid-template-columns:1fr auto;align-items:center;padding:16px 18px}.pill{display:inline-flex;align-items:center;gap:8px;font-weight:700}.dot{width:9px;height:9px;border-radius:50%;background:#64816f}.subtle{color:var(--muted);font-size:13px;margin-top:3px}.quick-grid{grid-template-columns:1fr 1fr}.quick{border:1px solid var(--line);background:var(--card);border-radius:18px;padding:18px;text-align:left;color:var(--ink)}.quick strong{display:block;font-size:17px;margin-bottom:4px}.quick span{color:var(--muted);font-size:13px}.btn{border:0;border-radius:14px;background:var(--accent);color:#fff;padding:13px 16px;font-weight:800}.btn.secondary{background:var(--soft);color:var(--ink)}.btn.danger{background:var(--danger)}.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}.form-card{padding:18px}.field{display:grid;gap:7px;margin-bottom:14px}.field label{font-weight:750;font-size:14px}.field input,.field select{width:100%;padding:13px;border:1px solid var(--line);border-radius:13px;background:#fff;color:var(--ink)}.status{min-height:22px;color:var(--muted);margin-top:10px}.upload-preview{height:240px;border:1px dashed #bdb8af;border-radius:18px;display:grid;place-items:center;overflow:hidden;background:#eeeae2;color:var(--muted);text-align:center}.upload-preview img{width:100%;height:100%;object-fit:contain;background:#151515}.toolbar{display:grid;gap:10px;margin-bottom:14px}.search{display:flex;gap:8px}.search input{flex:1;padding:13px 14px;border:1px solid var(--line);border-radius:14px;background:#fff}.chips{display:flex;gap:8px;overflow:auto;padding-bottom:2px}.chip{white-space:nowrap;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:9px 13px;border-radius:999px}.chip.active{background:var(--accent);color:#fff;border-color:var(--accent)}.library-summary{display:flex;justify-content:space-between;color:var(--muted);font-size:13px;margin:6px 2px 12px}.art-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.art-tile{padding:0;border:1px solid var(--line);border-radius:18px;background:var(--card);overflow:hidden;text-align:left;color:var(--ink);box-shadow:0 6px 20px rgba(33,38,35,.05)}.art-tile img{width:100%;aspect-ratio:3/4;object-fit:cover;background:#171717;display:block}.tile-body{padding:11px}.tile-title{font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.tile-meta{font-size:12px;color:var(--muted);margin-top:3px}.fav{color:#9a7730}.empty{padding:28px;text-align:center;color:var(--muted);background:var(--card);border-radius:18px;border:1px solid var(--line)}.schedule-row{padding:15px 0;border-bottom:1px solid var(--line)}.schedule-row:last-child{border:0}.schedule-row p{color:var(--muted);margin:5px 0 10px}.bottom-nav{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(820px,100%);display:grid;grid-template-columns:repeat(4,1fr);background:rgba(251,250,247,.96);border-top:1px solid var(--line);backdrop-filter:blur(14px);padding:8px 8px calc(8px + env(safe-area-inset-bottom));z-index:20}.nav{border:0;background:transparent;color:var(--muted);padding:8px 3px;font-size:12px}.nav strong{display:block;font-size:20px;line-height:1.1}.nav.active{color:var(--accent);font-weight:800}.modal{position:fixed;inset:0;background:rgba(20,24,22,.62);z-index:50;display:grid;align-items:end}.sheet{background:var(--paper);max-height:92vh;overflow:auto;border-radius:28px 28px 0 0;padding:16px 18px calc(24px + env(safe-area-inset-bottom));box-shadow:0 -18px 50px rgba(0,0,0,.2)}.sheet-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.close{border:0;background:var(--soft);width:38px;height:38px;border-radius:50%}.detail-img{width:100%;max-height:48vh;object-fit:contain;background:#151515;border-radius:18px}.detail-title{font:700 28px/1.1 Georgia,serif;margin:16px 0 5px}.detail-meta{color:var(--muted);margin:0 0 14px}.species{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px}.species span{background:var(--soft);padding:7px 10px;border-radius:999px;font-size:13px}.action-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.action-grid .btn{width:100%}.rename-row{display:flex;gap:8px;margin:12px 0}.rename-row input{flex:1;padding:12px;border-radius:12px;border:1px solid var(--line)}.journal-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:14px}.journal-head p{margin:5px 0 0;color:var(--muted)}.journal-month{margin:22px 0 10px;font:700 21px/1.1 Georgia,serif}.journal-list{display:grid;gap:12px}.journal-entry{display:grid;grid-template-columns:92px 1fr;gap:14px;align-items:center;border:1px solid var(--line);background:var(--card);border-radius:18px;padding:10px;text-align:left;color:var(--ink)}.journal-entry img{width:92px;height:116px;object-fit:cover;border-radius:12px;background:#171717}.journal-date{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:800}.journal-entry h3{margin:5px 0 6px;font:700 20px/1.1 Georgia,serif}.journal-birds{color:var(--muted);font-size:13px;line-height:1.45}.brief-block{margin:14px 0;padding:14px;background:var(--soft);border-radius:15px}.brief-block h4{margin:0 0 6px}.brief-block p{margin:0;color:var(--muted);line-height:1.5}.exhibition-panel{margin:18px 0;padding:18px;background:var(--card);border:1px solid var(--line);border-radius:20px}.exhibition-kicker{text-transform:uppercase;letter-spacing:.12em;font-size:11px;font-weight:800;color:var(--muted);margin:0 0 8px}.exhibition-panel h3{font:700 22px/1.15 Georgia,serif;margin:0 0 9px}.exhibition-panel p{margin:0;color:var(--muted);line-height:1.6}.exhibition-section{padding:16px 0;border-top:1px solid var(--line)}.exhibition-section:first-child{padding-top:0;border-top:0}.bird-groups{display:grid;gap:12px}.bird-group-label{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.09em;font-weight:800;color:var(--muted);margin-bottom:7px}.bird-role-list{display:flex;flex-wrap:wrap;gap:7px}.bird-role-list span{background:var(--soft);padding:7px 10px;border-radius:999px;font-size:13px}.bird-role-list.hero span{background:#e9dfc8}.exhibition-collection{font-weight:800;color:var(--ink)!important}.gallery-plaque{margin:14px 0 18px;padding:18px 18px 16px;background:#f1eee7;border-left:4px solid #9b8b70;border-radius:4px 16px 16px 4px}.gallery-plaque .detail-title{margin:0 0 7px}.gallery-plaque .detail-meta{margin:0 0 12px}.plaque-collection{font:italic 18px/1.3 Georgia,serif;color:var(--ink);margin:0 0 8px}.plaque-facts{display:flex;flex-wrap:wrap;gap:6px 10px;color:var(--muted);font-size:12px;line-height:1.45}.plaque-facts span+span:before{content:'·';margin-right:10px;color:#a49b8d}
@media(min-width:650px){.art-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.quick-grid{grid-template-columns:repeat(4,1fr)}.sheet{width:min(720px,100%);margin:0 auto;border-radius:28px 28px 0 0}}
</style>
</head>
<body>
<main class="app">
<header class="topbar"><div class="brand">Gallery</div><div class="version">v0.8.1</div></header>
<section id="home" class="panel active">
  <div class="card hero" id="hero"><div class="hero-empty">Loading gallery…</div></div>
  <div class="card mode-row section"><div><div class="pill" id="mode-pill"><span class="dot"></span>Automatic</div><div class="subtle" id="hero-subtle">Loading…</div></div><button id="end-override" class="btn secondary hidden">End now</button></div>
  <div id="assurance-card" class="card form-card section">
    <strong id="assurance-title">Checking daily artwork…</strong>
    <p id="assurance-message" class="subtle">GalleryOS is checking the current BirdCanvas artwork.</p>
  </div>
  <div class="section"><h2>Quick actions</h2><div class="quick-grid"><button class="quick" data-go="add"><strong>＋ Add artwork</strong><span>Upload from your phone</span></button><button class="quick" data-go="birdnet"><strong>BirdNET Import</strong><span>Upload detections and generate artwork</span></button><button class="quick" data-go="schedule"><strong>Calendar</strong><span>Plan a temporary display</span></button><button class="quick" data-go="library"><strong>Library</strong><span id="library-count">Browse artwork</span></button><button class="quick" data-filter="favourites"><strong>★ Favourites</strong><span id="fav-count">Your saved pieces</span></button><button class="quick" data-go="journal"><strong>BirdCanvas journal</strong><span>Browse the garden through time</span></button><button class="quick" data-go="settings"><strong>Display settings</strong><span>Hours, blackout and rotation</span></button><button class="quick" data-go="system"><strong>System status</strong><span>Health, backup and diagnostics</span></button></div></div>
  <div class="card form-card section"><strong>Next change</strong><div class="subtle" id="next-change">Loading…</div></div>
</section>
<section id="add" class="panel"><h2>Add artwork</h2><form id="upload-form" class="card form-card"><div id="upload-preview" class="upload-preview"><div><strong>No image selected</strong><br><span>JPG, PNG or WebP · up to 20 MB</span></div></div><div class="field section"><label>Image</label><input id="upload-image" name="image" type="file" accept="image/jpeg,image/png,image/webp" required></div><div class="field"><label>Title</label><input id="upload-title" maxlength="120" placeholder="Custom artwork"></div><div class="field"><label>What should happen?</label><select id="upload-action"><option value="now">Display now</option><option value="schedule">Schedule it</option><option value="save">Save to library</option></select></div><div id="upload-now"><div class="field"><label>Display for</label><select id="upload-duration"><option value="30">30 minutes</option><option value="60" selected>1 hour</option><option value="180">3 hours</option><option value="360">6 hours</option><option value="720">12 hours</option><option value="1440">24 hours</option></select></div></div><div id="upload-schedule" class="hidden"><div class="field"><label>Starts</label><input id="upload-start" type="datetime-local"></div><div class="field"><label>Ends</label><input id="upload-end" type="datetime-local"></div></div><button id="upload-button" class="btn" type="submit">Upload and display</button><div id="upload-status" class="status"></div></form></section>
<section id="birdnet" class="panel">
  <h2>BirdNET Import</h2>

  <form id="birdnet-form" class="card form-card">
    <div class="field">
      <label>BirdNET Live ZIP export</label>
      <input id="birdnet-zip" type="file" accept=".zip" required>
    </div>

    <button class="btn" type="submit">
      Import BirdNET Session
    </button>

    <button
      id="generate-artwork-button"
      class="btn secondary"
      type="button"
      style="margin-top:12px;">
      🎨 Generate Today's Artwork
    </button>

    <div id="birdnet-status" class="status"></div>
  </form>
</section><section id="schedule" class="panel"><h2>Schedule</h2><div class="card form-card"><div class="field"><label>Artwork</label><select id="schedule-artwork"></select></div><div class="field"><label>Starts</label><input id="schedule-start" type="datetime-local"></div><div class="field"><label>Ends</label><input id="schedule-end" type="datetime-local"></div><button id="schedule-button" class="btn">Add schedule</button><div id="schedule-status" class="status"></div></div><div class="section"><h2>Upcoming and active</h2><div id="schedules" class="card form-card"></div></div></section>
<section id="journal" class="panel"><div class="journal-head"><div><h2>BirdCanvas journal</h2><p>A dated record of the artwork and birds from your garden.</p></div></div><div id="journal-content"></div></section>
<section id="library" class="panel"><h2>Library</h2><div class="toolbar"><div class="search"><input id="search" type="search" placeholder="Search title or bird species"></div><div class="chips" id="chips"><button class="chip active" data-filter="all">All</button><button class="chip" data-filter="birdcanvas">BirdCanvas</button><button class="chip" data-filter="custom">Custom</button><button class="chip" data-filter="favourites">Favourites</button><button class="chip" data-filter="hidden">Hidden</button></div></div><div class="library-summary"><span id="result-count">0 artworks</span><span id="collection-summary"></span></div><div id="art-grid" class="art-grid"></div></section>


<section id="system" class="panel">
  <h2>System status</h2>
  <div id="health-card" class="card form-card"><p>Checking GalleryOS…</p></div>
  <div class="card form-card section">
    <button id="create-backup" class="btn" type="button">Create backup</button>
    <button id="download-diagnostics" class="btn secondary" type="button">Download diagnostics</button>
    <div id="system-action-status" class="status"></div>
  </div>
</section>
<section id="settings" class="panel">
  <h2>Display settings</h2>
  <form id="display-settings-form" class="card form-card">
    <div class="field">
      <label><input id="display-enabled" type="checkbox"> Display enabled</label>
    </div>
    <div class="field">
      <label><input id="use-display-hours" type="checkbox"> Use overnight display hours</label>
    </div>
    <div id="display-hours-fields">
      <div class="field"><label>Black screen from</label><input id="sleep-start" type="time"></div>
      <div class="field"><label>Wake display at</label><input id="wake-time" type="time"></div>
    </div>
    <div class="field">
      <label><input id="wake-for-overrides" type="checkbox"> Wake for scheduled and temporary artwork</label>
    </div>
    <div class="field">
      <label>Screen rotation</label>
      <select id="display-rotation">
        <option value="0">Standard</option>
        <option value="90">90° clockwise</option>
        <option value="270">90° anticlockwise</option>
      </select>
    </div>
    <div class="field">
      <label>Artwork fit</label>
      <select id="display-fit-mode">
        <option value="contain">Show the whole artwork</option>
        <option value="cover">Fill the screen and crop edges</option>
      </select>
    </div>
    <div class="field">
      <label>Background behind artwork</label>
      <select id="display-background">
        <option value="black">Black</option>
        <option value="soft_black">Soft black</option>
        <option value="white">White</option>
      </select>
    </div>
    <div class="field">
      <label>Artwork transition</label>
      <select id="display-transition">
        <option value="fade">Gentle fade</option>
        <option value="slow_fade">Slow gallery fade</option>
        <option value="cut">Instant change</option>
      </select>
    </div>
    <div class="field">
      <label>Check for changes</label>
      <select id="display-poll-seconds">
        <option value="2">Every 2 seconds</option>
        <option value="5">Every 5 seconds</option>
        <option value="10">Every 10 seconds</option>
        <option value="30">Every 30 seconds</option>
      </select>
    </div>
    <button class="btn" type="submit">Save display settings</button>
    <div id="display-settings-status" class="status"></div>
  </form>
  <div class="card form-card section">
    <strong>How overnight mode works</strong>
    <p class="subtle">GalleryOS shows a pure black screen during sleeping hours. An active scheduled or temporary artwork can wake it automatically when that option is enabled.</p>
  </div>
</section>

</main>
<nav class="bottom-nav"><button class="nav active" data-go="home"><strong>⌂</strong>Home</button><button class="nav" data-go="add"><strong>＋</strong>Add</button><button class="nav" data-go="schedule"><strong>◷</strong>Schedule</button><button class="nav" data-go="library"><strong>▦</strong>Library</button></nav>
<div id="detail-modal" class="modal hidden"><div class="sheet"><div class="sheet-head"><strong>Exhibition</strong><button id="detail-close" class="close">×</button></div><img id="detail-img" class="detail-img" alt=""><div id="detail-plaque" class="gallery-plaque"><h2 id="detail-title" class="detail-title"></h2><p id="detail-meta" class="detail-meta"></p><p id="detail-plaque-collection" class="plaque-collection"></p><div class="plaque-facts"><span id="detail-plaque-medium"></span><span id="detail-plaque-origin"></span></div></div><div id="detail-species" class="species"></div><div id="detail-exhibition" class="exhibition-panel hidden"><div class="exhibition-section"><p class="exhibition-kicker">Curator's Notes</p><p id="detail-narrative"></p></div><div id="detail-bird-groups" class="exhibition-section bird-groups"></div><div class="exhibition-section"><p class="exhibition-kicker">Collection</p><h3 id="detail-collection"></h3><p id="detail-mood"></p></div><div class="exhibition-section"><p class="exhibition-kicker">Composition</p><p id="detail-composition"></p></div></div><div class="rename-row"><input id="detail-rename" maxlength="120"><button id="rename-button" class="btn secondary">Rename</button></div><div class="field"><label for="detail-mount">Mount presentation</label><select id="detail-mount"><option value="auto">Automatic</option><option value="white_mount">White mount</option><option value="black_mount">Black mount</option><option value="no_mount">No mount</option></select><div id="mount-reason" class="subtle"></div></div><div class="action-grid"><button id="apply-mount-button" class="btn secondary">Apply mount</button><button id="display-button" class="btn">Display now</button><button id="schedule-detail-button" class="btn secondary">Schedule</button><button id="favourite-button" class="btn secondary">Favourite</button><button id="hide-button" class="btn secondary">Hide</button><button id="delete-button" class="btn danger hidden">Delete upload</button></div></div></div>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];let libraryData={artworks:[]},displayData=null,currentFilter='all',selectedArtwork=null;
async function api(url){const r=await fetch(url,{cache:'no-store'}),d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');return d}async function post(url,p={}){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}),d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');return d}
function localIso(d){const p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`}
function fmt(v){if(!v)return '';const d=new Date(v);return Number.isNaN(d.getTime())?v:d.toLocaleString([], {dateStyle:'medium',timeStyle:'short'})}
function formatDate(v){if(!v)return '';const d=new Date(`${String(v).slice(0,10)}T12:00:00`);return Number.isNaN(d.getTime())?v:d.toLocaleDateString([], {day:'numeric',month:'long',year:'numeric'})}
function openPanel(id){$$('.panel').forEach(p=>p.classList.toggle('active',p.id===id));$$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.go===id));window.scrollTo({top:0,behavior:'smooth'})}
$$('[data-go]').forEach(b=>b.onclick=()=>openPanel(b.dataset.go));$$('[data-filter]').forEach(b=>b.onclick=()=>{currentFilter=b.dataset.filter;openPanel('library');setFilter(currentFilter)});
function controlImageUrl(artwork){
  if(!artwork||!artwork.image_url)return '';
  const revision=artwork.display_revision||artwork.revision||artwork.created_at||Date.now();
  const separator=artwork.image_url.includes('?')?'&':'?';
  return `${artwork.image_url}${separator}v=${encodeURIComponent(revision)}`;
}
function renderHero(s){
  displayData=s;
  const box=$('#hero'),a=s.artwork;
  box.replaceChildren();

  if(!a){
    box.innerHTML='<div class="hero-empty">No valid BirdCanvas artwork is available.</div>';
  }else{
    const img=document.createElement('img');
    img.src=controlImageUrl(a);
    const grad=document.createElement('div');
    grad.className='hero-gradient';
    const label=document.createElement('div');
    label.className='hero-label';

    const modeLabel=
      s.mode==='automatic'?'Current BirdCanvas':
      s.mode==='fallback'?'BirdCanvas fallback':
      s.mode==='scheduled'?'Scheduled artwork':
      'Temporary artwork';

    label.innerHTML=`<div class="eyebrow">${modeLabel}</div><h1>${escapeHtml(a.title||a.id)}</h1><p>${a.collection==='birdcanvas'?(a.observation_date||'BirdCanvas'):'Custom collection'}</p>`;
    box.append(img,grad,label);
  }

  const modeText=
    s.mode==='automatic'?'Current BirdCanvas':
    s.mode==='fallback'?'BirdCanvas fallback':
    s.mode==='scheduled'?'Scheduled':
    'Temporary override';

  $('#mode-pill').innerHTML=`<span class="dot"></span>${modeText}`;

  $('#hero-subtle').textContent=
    s.mode==='temporary_override'?`Ends ${fmt(s.override.ends_at)}`:
    s.mode==='scheduled'?`Returns to the current BirdCanvas artwork ${fmt(s.schedule.ends_at)}`:
    s.mode==='fallback'?'The most recent valid BirdCanvas artwork is being protected.':
    'The newest valid BirdCanvas artwork is controlling the display.';

  $('#end-override').classList.toggle('hidden',s.mode!=='temporary_override');

  const assurance=s.assurance||{};
  const assuranceTitle={
    current:'Daily artwork current',
    late:'Daily artwork delayed',
    fallback:'Using BirdCanvas fallback',
    missing:'BirdCanvas artwork unavailable'
  }[assurance.status]||'Current artwork assurance';

  $('#assurance-title').textContent=assuranceTitle;
  $('#assurance-message').textContent=assurance.message||(
    s.mode==='scheduled'||s.mode==='temporary_override'
      ?'The current BirdCanvas artwork will return automatically when this temporary artwork ends.'
      :'GalleryOS is protecting the current BirdCanvas artwork.'
  );
}
function renderNext(schedules){const future=schedules.filter(x=>new Date(x.starts_at)>new Date()).sort((a,b)=>new Date(a.starts_at)-new Date(b.starts_at));$('#next-change').textContent=displayData?.mode==='temporary_override'?`Return to automatic mode ${fmt(displayData.override.ends_at)}`:displayData?.mode==='scheduled'?`Current schedule ends ${fmt(displayData.schedule.ends_at)}`:future.length?`${future[0].artwork.title} · ${fmt(future[0].starts_at)}`:'When the next daily BirdCanvas artwork is published'}
function setFilter(filter){currentFilter=filter;$$('.chip').forEach(c=>c.classList.toggle('active',c.dataset.filter===filter));renderLibrary()}
function filteredArtworks(){const q=$('#search').value.trim().toLowerCase();return libraryData.artworks.filter(a=>{const matchesFilter=currentFilter==='all'?!a.hidden:currentFilter==='favourites'?a.favourite&&!a.hidden:currentFilter==='hidden'?a.hidden:a.collection===currentFilter&&!a.hidden;const hay=[a.title,a.collection,...(a.species||[])].join(' ').toLowerCase();return matchesFilter&&(!q||hay.includes(q))})}
function monthLabel(value){const d=new Date(`${value||''}T12:00:00`);return Number.isNaN(d.getTime())?'Undated':d.toLocaleDateString(undefined,{month:'long',year:'numeric'})}
function renderJournal(){const box=$('#journal-content'),items=libraryData.artworks.filter(a=>a.collection==='birdcanvas'&&!a.hidden).sort((a,b)=>(b.observation_date||b.created_at).localeCompare(a.observation_date||a.created_at));box.replaceChildren();if(!items.length){box.innerHTML='<div class="empty">No BirdCanvas artwork has been archived yet.</div>';return}let activeMonth='';for(const a of items){const month=monthLabel(a.observation_date||a.created_at.slice(0,10));if(month!==activeMonth){activeMonth=month;const heading=document.createElement('h3');heading.className='journal-month';heading.textContent=month;box.append(heading)}const entry=document.createElement('button');entry.className='journal-entry';const birds=(a.species||[]);entry.innerHTML=`<img src="${a.image_url}" alt=""><div><div class="journal-date">${escapeHtml(a.observation_date||a.created_at.slice(0,10))}</div><h3>${escapeHtml(a.title)}</h3><div class="journal-birds">${birds.length?`${birds.length} species · ${escapeHtml(birds.slice(0,4).join(', '))}${birds.length>4?'…':''}`:'No species recorded'}</div></div>`;entry.onclick=()=>openDetail(a);box.append(entry)}}
function renderLibrary(){const items=filteredArtworks(),grid=$('#art-grid');grid.replaceChildren();$('#result-count').textContent=`${items.length} artwork${items.length===1?'':'s'}`;const bc=libraryData.artworks.filter(a=>a.collection==='birdcanvas').length,cu=libraryData.artworks.filter(a=>a.collection==='custom').length;$('#collection-summary').textContent=`${bc} BirdCanvas · ${cu} custom`;if(!items.length){grid.innerHTML='<div class="empty" style="grid-column:1/-1">No artwork matches this view.</div>';return}for(const a of items){const tile=document.createElement('button');tile.className='art-tile';tile.innerHTML=`<img src="${a.image_url}" alt=""><div class="tile-body"><div class="tile-title">${a.favourite?'<span class="fav">★</span> ':''}${escapeHtml(a.title)}</div><div class="tile-meta">${a.collection==='birdcanvas'?(a.observation_date||'BirdCanvas'):'Custom'}</div></div>`;tile.onclick=()=>openDetail(a);grid.append(tile)}}
function openDetail(a){
  selectedArtwork=a;
  $('#detail-img').src=controlImageUrl(a);
  $('#detail-title').textContent=a.title;
  const detailDate=a.observation_date?formatDate(a.observation_date):fmt(a.created_at);
  $('#detail-meta').textContent=detailDate;
  const exhibition=a.exhibition||{};
  const brief=a.creative_brief||{};
  const plaqueCollection=exhibition.collection||a.creative_collection||brief.collection||'';
  $('#detail-plaque-collection').textContent=plaqueCollection;
  $('#detail-plaque-collection').classList.toggle('hidden',!plaqueCollection);
  $('#detail-plaque-medium').textContent=a.collection==='birdcanvas'?'BirdCanvas Collection · Digital artwork':'GalleryOS Custom Collection · Digital artwork';
  const visitorCount=Number(exhibition.visitor_count)||(a.species||[]).length;
  $('#detail-plaque-origin').textContent=a.collection==='birdcanvas'?(visitorCount?`Created from ${visitorCount} garden visitor${visitorCount===1?'':'s'}`:'Created from garden observations'):'Added to the GalleryOS library';
  $('#detail-rename').value=a.title;
  const sp=$('#detail-species');
  const showFlatSpecies=a.collection!=='birdcanvas'&&(a.species||[]).length;
  sp.replaceChildren(...(a.species||[]).map(x=>Object.assign(document.createElement('span'),{textContent:x})));
  sp.classList.toggle('hidden',!showFlatSpecies);

  const narrative=exhibition.narrative||'';
  const collection=exhibition.collection||a.creative_collection||brief.collection||'';
  const mood=a.mood||brief.mood||'';
  const composition=exhibition.composition||brief.composition||'';
  const exhibitionPanel=$('#detail-exhibition');
  const hasExhibition=a.collection==='birdcanvas'&&(narrative||collection||mood||composition);
  exhibitionPanel.classList.toggle('hidden',!hasExhibition);
  $('#detail-narrative').textContent=narrative;
  $('#detail-collection').textContent=collection;
  $('#detail-mood').textContent=mood;
  $('#detail-composition').textContent=composition;

  const groups=$('#detail-bird-groups');
  groups.replaceChildren();
  const birdGroups=[
    ['Featured birds',exhibition.hero_birds||brief.hero_birds||[],'hero'],
    ['Character birds',exhibition.character_birds||brief.character_birds||[],''],
    ['Supporting birds',exhibition.supporting_birds||brief.supporting_birds||[],'']
  ];
  for(const [label,birds,kind] of birdGroups){
    if(!birds.length)continue;
    const group=document.createElement('div');
    const heading=document.createElement('span');
    heading.className='bird-group-label';
    heading.textContent=label;
    const list=document.createElement('div');
    list.className=`bird-role-list ${kind}`.trim();
    list.replaceChildren(...birds.map(name=>Object.assign(document.createElement('span'),{textContent:name})));
    group.append(heading,list);
    groups.append(group);
  }
  groups.classList.toggle('hidden',!groups.children.length);

  $('#favourite-button').textContent=a.favourite?'Remove favourite':'Favourite';
  $('#hide-button').textContent=a.hidden?'Unhide':'Hide';
  $('#delete-button').classList.toggle('hidden',a.collection!=='custom');
  const presentation=a.presentation||{};
  $('#detail-mount').value=presentation.mode||'auto';
  $('#mount-reason').textContent=presentation.decision_reason||'Automatic chooses the most suitable neutral mount from the artwork edges.';
  $('#detail-modal').classList.remove('hidden');
}
function closeDetail(){$('#detail-modal').classList.add('hidden');selectedArtwork=null}$('#detail-close').onclick=closeDetail;$('#detail-modal').onclick=e=>{if(e.target.id==='detail-modal')closeDetail()};
$('#display-button').onclick=async()=>{await post('/api/override',{artwork_id:selectedArtwork.id,duration_minutes:60});closeDetail();openPanel('home');await refresh()};
$('#schedule-detail-button').onclick=()=>{$('#schedule-artwork').value=selectedArtwork.id;closeDetail();openPanel('schedule')};
$('#favourite-button').onclick=async()=>{await post('/api/artwork/update',{artwork_id:selectedArtwork.id,favourite:!selectedArtwork.favourite});await refresh();openDetail(libraryData.artworks.find(a=>a.id===selectedArtwork.id))};
$('#hide-button').onclick=async()=>{await post('/api/artwork/update',{artwork_id:selectedArtwork.id,hidden:!selectedArtwork.hidden});closeDetail();await refresh()};
$('#rename-button').onclick=async()=>{const title=$('#detail-rename').value.trim();if(!title)return;await post('/api/artwork/update',{artwork_id:selectedArtwork.id,title});await refresh();openDetail(libraryData.artworks.find(a=>a.id===selectedArtwork.id))};
$('#apply-mount-button').onclick=async()=>{const button=$('#apply-mount-button'),mode=$('#detail-mount').value;button.disabled=true;button.textContent='Applying…';try{await post('/api/artwork/presentation',{artwork_id:selectedArtwork.id,mode});await refresh();openDetail(libraryData.artworks.find(a=>a.id===selectedArtwork.id))}catch(e){alert(e.message)}finally{button.disabled=false;button.textContent='Apply mount'}};
$('#delete-button').onclick=async()=>{if(!confirm('Permanently delete this uploaded artwork?'))return;await post('/api/custom/delete',{artwork_id:selectedArtwork.id});closeDetail();await refresh()};
$('#search').addEventListener('input',renderLibrary);$$('.chip').forEach(c=>c.onclick=()=>setFilter(c.dataset.filter));
function fillScheduleOptions(){const selected=$('#schedule-artwork').value;$('#schedule-artwork').replaceChildren();for(const a of libraryData.artworks.filter(a=>!a.hidden)){const o=document.createElement('option');o.value=a.id;o.textContent=`${a.title} · ${a.collection==='birdcanvas'?'BirdCanvas':'Custom'}`;$('#schedule-artwork').append(o)}if([...$('#schedule-artwork').options].some(o=>o.value===selected))$('#schedule-artwork').value=selected}
function renderSchedules(items){const box=$('#schedules');box.replaceChildren();if(!items.length){box.innerHTML='<p class="subtle">No upcoming schedules.</p>';return}for(const s of items){const row=document.createElement('div');row.className='schedule-row';row.innerHTML=`<strong>${escapeHtml(s.artwork.title)}</strong><p>${fmt(s.starts_at)} → ${fmt(s.ends_at)}</p>`;const del=document.createElement('button');del.className='btn ghost';del.textContent='Delete schedule';del.onclick=async()=>{if(confirm('Delete this schedule?')){await post('/api/schedules/delete',{schedule_id:s.id});await refresh()}};row.append(del);box.append(row)}}
function escapeHtml(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function renderDisplaySettings(settings){
  $('#display-enabled').checked=settings.enabled!==false;
  $('#use-display-hours').checked=!!settings.use_display_hours;
  $('#sleep-start').value=settings.sleep_start||'23:00';
  $('#wake-time').value=settings.wake_time||'07:00';
  $('#wake-for-overrides').checked=settings.wake_for_overrides!==false;
  $('#display-rotation').value=String(settings.rotation||0);
  $('#display-fit-mode').value=settings.fit_mode||'contain';
  $('#display-background').value=settings.background||'black';
  $('#display-transition').value=settings.transition||'fade';
  $('#display-poll-seconds').value=String(settings.poll_seconds||5);
  $('#display-hours-fields').classList.toggle('hidden',!settings.use_display_hours);
}
async function refresh(){try{const [display,library,schedules,settings]=await Promise.all([api('/api/display'),api('/api/library'),api('/api/schedules'),api('/api/display/settings')]);libraryData=library;renderDisplaySettings(settings);renderHero(display);fillScheduleOptions();renderLibrary();renderJournal();renderSchedules(schedules.schedules);renderNext(schedules.schedules);$('#library-count').textContent=`${library.artworks.length} artworks`;$('#fav-count').textContent=`${library.artworks.filter(a=>a.favourite).length} favourites`}catch(e){console.error(e)}}
$('#end-override').onclick=async()=>{await post('/api/override/cancel');await refresh()};
$('#upload-action').onchange=()=>{const v=$('#upload-action').value;$('#upload-now').classList.toggle('hidden',v!=='now');$('#upload-schedule').classList.toggle('hidden',v!=='schedule');$('#upload-button').textContent=v==='now'?'Upload and display':v==='schedule'?'Upload and schedule':'Save to library'};
let previewUrl=null;$('#upload-image').onchange=e=>{const f=e.target.files[0];if(previewUrl)URL.revokeObjectURL(previewUrl);if(!f)return;previewUrl=URL.createObjectURL(f);$('#upload-preview').innerHTML=`<img src="${previewUrl}" alt="Preview">`;if(!$('#upload-title').value.trim())$('#upload-title').value=f.name.replace(/\.[^.]+$/,'').replace(/[-_]+/g,' ')};
$('#upload-form').onsubmit=async e=>{e.preventDefault();const file=$('#upload-image').files[0],action=$('#upload-action').value,status=$('#upload-status');if(!file){status.textContent='Choose an image first.';return}const form=new FormData();form.append('image',file);form.append('title',$('#upload-title').value);form.append('show_now',action==='now'?'true':'false');form.append('duration_minutes',$('#upload-duration').value);try{status.textContent='Uploading…';const r=await fetch('/api/upload',{method:'POST',body:form}),d=await r.json();if(!r.ok)throw new Error(d.error||'Upload failed');if(action==='schedule')await post('/api/schedules',{artwork_id:d.artwork.id,starts_at:$('#upload-start').value,ends_at:$('#upload-end').value});status.textContent=action==='now'?'Artwork is now displayed.':action==='schedule'?'Artwork uploaded and scheduled.':'Artwork saved to library.';await refresh();setTimeout(()=>openPanel(action==='now'?'home':action==='schedule'?'schedule':'library'),700)}catch(err){status.textContent=err.message}};$('#birdnet-form').onsubmit = async e => {
    e.preventDefault();

    const file = $('#birdnet-zip').files[0];
    const status = $('#birdnet-status');

    if (!file) {
        status.textContent = 'Choose a BirdNET ZIP export first.';
        return;
    }

    const form = new FormData();
    form.append('zip_file', file);

    try {
        status.textContent = 'Importing BirdNET session...';

        const response = await fetch('/api/birdnet/upload', {
            method: 'POST',
            body: form
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Import failed');
        }

        status.textContent =
            'BirdNET session imported successfully. You can now generate today\'s artwork.';

    } catch (err) {
        status.textContent = err.message;
    }
};$('#generate-artwork-button').onclick = async () => {
    const status = $('#birdnet-status');

    try {
        status.textContent = 'Generating artwork...';

        const response = await fetch('/api/birdnet/generate', {
            method: 'POST'
        });

        // We don't wait for JSON because artwork generation can take several minutes
        // and the browser may time out before a response is returned.
        if (!response.ok) {
            status.textContent = 'Artwork generation started.';
            return;
        }

        status.textContent = 'Artwork generation started. This may take a few minutes.';

    } catch (err) {
        // Even if the request times out, the server is probably still generating.
        status.textContent =
            'Artwork generation has been started. Check the display in a few minutes.';
    }
};
$('#schedule-button').onclick=async()=>{try{await post('/api/schedules',{artwork_id:$('#schedule-artwork').value,starts_at:$('#schedule-start').value,ends_at:$('#schedule-end').value});$('#schedule-status').textContent='Schedule added.';await refresh()}catch(e){$('#schedule-status').textContent=e.message}};


function healthLabel(status){if(status==='ok')return 'Healthy';if(status==='warning')return 'Attention';return 'Problem';}
function renderHealth(report){const checks=report.checks||{};const rows=Object.entries(checks).map(([name,value])=>`<div class="schedule-row"><div><strong>${escapeHtml(name.replace('_',' '))}</strong><p>${escapeHtml(healthLabel(value.status))}</p></div><span>${escapeHtml(value.message||'')}</span></div>`).join('');$('#health-card').innerHTML=`<strong>GalleryOS ${escapeHtml(report.version||'')}</strong><p class="subtle">Checked ${escapeHtml(formatDate(report.checked_at))}</p>${rows}`;}
async function refreshHealth(){try{renderHealth(await api('/api/health'));}catch(error){$('#health-card').innerHTML=`<p>${escapeHtml(error.message)}</p>`;}}
$('#create-backup').onclick=async()=>{const status=$('#system-action-status');try{status.textContent='Creating backup…';const result=await post('/api/backup',{});status.innerHTML=`Backup ready. <a href="${result.download_url}">Download backup</a>`;}catch(error){status.textContent=error.message;}};
$('#download-diagnostics').onclick=async()=>{const status=$('#system-action-status');try{status.textContent='Creating diagnostics…';const result=await post('/api/diagnostics',{});window.location.href=result.download_url;status.textContent='Diagnostics download ready.';}catch(error){status.textContent=error.message;}};

$('#use-display-hours').onchange=()=>{
  $('#display-hours-fields').classList.toggle('hidden',!$('#use-display-hours').checked);
};
$('#display-settings-form').onsubmit=async event=>{
  event.preventDefault();
  const status=$('#display-settings-status');
  try{
    status.textContent='Saving…';
    await post('/api/display/settings',{
      enabled:$('#display-enabled').checked,
      use_display_hours:$('#use-display-hours').checked,
      sleep_start:$('#sleep-start').value,
      wake_time:$('#wake-time').value,
      wake_for_overrides:$('#wake-for-overrides').checked,
      rotation:Number($('#display-rotation').value),
      fit_mode:$('#display-fit-mode').value,
      background:$('#display-background').value,
      transition:$('#display-transition').value,
      transition_seconds:{fade:1.1,slow_fade:2.5,cut:0}[$('#display-transition').value],
      poll_seconds:Number($('#display-poll-seconds').value)
    });
    status.textContent='Display settings saved.';
    await refresh();
  }catch(error){
    status.textContent=error.message;
  }
};

const st=new Date(Date.now()+3600000),en=new Date(Date.now()+7200000);['schedule-start','upload-start'].forEach(id=>$('#'+id).value=localIso(st));['schedule-end','upload-end'].forEach(id=>$('#'+id).value=localIso(en));refresh();setInterval(refresh,15000);
</script>
</body></html>'''


if __name__ == "__main__":
    build_display_page()
