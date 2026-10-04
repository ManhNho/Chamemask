const CACHE='chamemask-v1';
const ASSETS=['./','./index.html','./icon.svg','./face_catalog.json'];

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});

self.addEventListener('fetch',e=>{
  const url=new URL(e.request.url);
  if(url.origin==='https://thispersonnotexist.org'){
    e.respondWith(fetch(e.request).then(r=>{
      if(r.ok){const c=r.clone();caches.open(CACHE).then(cache=>cache.put(e.request,c));}
      return r;
    }).catch(()=>caches.match(e.request)));
    return;
  }
  if(url.origin===location.origin){
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{
      if(resp.ok){const c=resp.clone();caches.open(CACHE).then(cache=>cache.put(e.request,c));}
      return resp;
    })));
    return;
  }
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
