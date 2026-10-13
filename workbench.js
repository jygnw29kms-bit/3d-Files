import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';
import {OrbitControls} from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';
import {STLLoader} from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/loaders/STLLoader.js';

const qs=s=>document.querySelector(s), qsa=s=>[...document.querySelectorAll(s)];
const menuBtn=qs('#menuBtn'), topnav=qs('#topnav'), search=qs('#searchInput'), noResults=qs('#noResults');
let filter='all';
function norm(v){return(v||'').toLocaleLowerCase('de-DE').normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
function apply(){const q=norm(search.value);let shown=0;qsa('.print-card').forEach(c=>{const hay=norm(c.textContent+' '+c.dataset.tags);const ok=(filter==='all'||hay.includes(filter))&&(!q||hay.includes(q));c.hidden=!ok;if(ok)shown++});noResults.hidden=shown>0}
qsa('.filter').forEach(b=>b.addEventListener('click',()=>{qsa('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');filter=b.dataset.filter;apply()}));
search?.addEventListener('input',apply);menuBtn?.addEventListener('click',()=>{const o=topnav.classList.toggle('open');menuBtn.setAttribute('aria-expanded',String(o))});

const host=qs('#viewerCanvas');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x050706);
const camera=new THREE.PerspectiveCamera(45,1,.1,5000);camera.position.set(160,120,180);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;host.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.autoRotate=false;controls.autoRotateSpeed=1.2;
scene.add(new THREE.HemisphereLight(0xd7ffef,0x101410,2.4));const key=new THREE.DirectionalLight(0xd7ff3f,3.1);key.position.set(140,180,120);scene.add(key);const rim=new THREE.DirectionalLight(0x65d9ff,2.0);rim.position.set(-150,80,-120);scene.add(rim);
const grid=new THREE.GridHelper(420,28,0x394239,0x1a201b);scene.add(grid);
let mesh=null, boxHelper=null;
function resize(){const w=host.clientWidth,h=Math.max(390,host.clientHeight);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(resize).observe(host);resize();
function frameObject(object){const box=new THREE.Box3().setFromObject(object),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3());const max=Math.max(size.x,size.y,size.z);camera.position.copy(center).add(new THREE.Vector3(max*1.5,max*.9,max*1.5));controls.target.copy(center);camera.near=Math.max(max/1000,.01);camera.far=max*100;camera.updateProjectionMatrix();controls.update();return size}
async function loadSTL(url,name){qs('.viewer-idle')?.remove();if(mesh){scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose()}if(boxHelper){scene.remove(boxHelper);boxHelper=null}qs('#vName').textContent='LOADING…';const loader=new STLLoader();loader.load(url,g=>{g.computeVertexNormals();const mat=new THREE.MeshStandardMaterial({color:0xcff23c,metalness:.16,roughness:.48});mesh=new THREE.Mesh(g,mat);g.center();mesh.rotation.x=-Math.PI/2;scene.add(mesh);boxHelper=new THREE.BoxHelper(mesh,0x65d9ff);scene.add(boxHelper);const s=frameObject(mesh);qs('#vName').textContent=name;qs('#vTriangles').textContent=Math.floor(g.attributes.position.count/3).toLocaleString('de-DE');qs('#vSize').textContent=`${s.x.toFixed(1)} / ${s.y.toFixed(1)} / ${s.z.toFixed(1)} mm`;host.scrollIntoView({behavior:'smooth',block:'center'})},undefined,e=>{console.error(e);qs('#vName').textContent='LOAD ERROR'})}
qsa('.js-view').forEach(b=>b.addEventListener('click',()=>loadSTL(b.dataset.stl,b.dataset.name)));
qs('#autoRotate')?.addEventListener('click',e=>{controls.autoRotate=!controls.autoRotate;e.currentTarget.classList.toggle('active',controls.autoRotate)});
(function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera)})();

fetch(window.PRINTBENCH?.api||'api.php',{cache:'no-store'}).then(r=>r.json()).then(data=>{document.documentElement.dataset.api='online';console.info('PRINTBENCH API',data)}).catch(()=>{document.documentElement.dataset.api='offline'});
