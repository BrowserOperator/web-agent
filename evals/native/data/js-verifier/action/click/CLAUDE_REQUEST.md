# Claude Code: Generate Validation JavaScript

## Objective
Type "DevTools automation" in the search box and then click the "Google Search" button

## Task
Analyze the DOM changes and generate JavaScript validation code.

## Files to Analyze

### Primary Analysis (Semantic Changes)
- **CHANGES**: native/data/js-verifier/action/click/changes.json - Structured semantic changes
- **BEFORE**: native/data/js-verifier/action/click/before.json - DOM snapshot before action (for reference)
- **AFTER**: native/data/js-verifier/action/click/after.json - DOM snapshot after action (for reference)

### Supplementary (Optional)
- **BEFORE HTML**: native/data/js-verifier/action/click/before.html - HTML for manual inspection
- **AFTER HTML**: native/data/js-verifier/action/click/after.html - HTML for manual inspection
- **HTML DIFF**: native/data/js-verifier/action/click/diff.txt - Line-by-line HTML diff

## Detected Changes Summary

**Total Changes:** 107

**Changes by Type:**
- attr_modified: 4
- position_changed: 5
- text_changed: 22
- node_removed: 12
- attr_added: 15
- attr_removed: 3
- style_changed: 3
- node_added: 43

**Sample Changes:**

### node_added

**Path:** `HTML > BODY#gsr > SPAN.LoygGf > DIV.Xx7Mif`

**Path:** `HTML > BODY#gsr > H1.bNg8Rb`

**Path:** `HTML > BODY#gsr > A.gyPpGe`

**Path:** `HTML > BODY#gsr > A.gyPpGe`

**Path:** `HTML > BODY#gsr > A.gyPpGe`

### node_removed

**Path:** `HTML > HEAD`

**Path:** `HTML > HEAD`

**Path:** `HTML > BODY#gsr > DIV`

**Path:** `HTML > BODY#gsr > DIV > DIV.o3j99`

**Path:** `HTML > BODY#gsr > DIV > DIV.o3j99`

### text_changed

**Path:** `HTML > HEAD > TITLE`
**Details:**
  - before: `Google`
  - after: `DevTools automation - Google Search`

**Path:** `HTML > HEAD`
**Details:**
  - before: `@font-face{font-family:'Google Sans';font-style:normal;font-weight:400 700;font-display:optional;src:url(//fonts.gstatic.com/s/googlesans/v58/4UaRrENHsxJlGDuGo1OIlJfC6l_24rlCK1Yo_Iq2vgCIhM907w.woff2)format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}@font-face{font-family:'Roboto';font-style:normal;font-weight:400;font-display:optional;src:url(//fonts.gstatic.com/s/roboto/v18/KFOmCnqEu92Fr1Mu4mxKKTU1Kg.woff2)format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}@font-face{font-family:'Roboto';font-style:normal;font-weight:700;font-display:optional;src:url(//fonts.gstatic.com/s/roboto/v18/KFOlCnqEu92Fr1MmWUlfBBc4AMP6lQ.woff2)format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}`
  - after: `window._hst=Date.now();`

**Path:** `HTML > HEAD`
**Details:**
  - before: `(function(){var w=["Google Sans",[400,500,700],"Roboto",[400,700]];(function(){for(var a=0;a<w.length;a+=2)for(var d=w[a],e=w[a+1],b=0,c=void 0;c=e[b];++b)document.fonts.load(c+" 10pt "+d).catch(function(){})})();})();`
  - after: `(function(){var l='th';var ei='GHkiaZ7GIpulqtsPjNPduQg';var sr=10;(function(a,c,d){a="/gen_204?ei="+ei+"&sol="+a+"&atyp=i&sr="+(c===void 0?100:c);d&&(a+=d);if(navigator.sendBeacon!==void 0)navigator.sendBeacon(a);else{var b=new Image;b.onerror=b.onload=b.onabort=function(){b=null};b.src=a+"&sb=n&zx="+Date.now()}})(l,sr);})();`

**Path:** `HTML > HEAD`
**Details:**
  - before: `window._hst=Date.now();`
  - after: `(function(){var b=window.addEventListener;window.addEventListener=function(a,c,d){a!=="unload"&&b(a,c,d)};}).call(this);(function(){var _g={kEI:'GHkiaZ7GIpulqtsPjNPduQg',kEXPI:'31',kBL:'R79U',kOPI:89978449};(function(){var a;((a=window.google)==null?0:a.stvsc)?google.kEI=_g.kEI:window.google=_g;}).call(this);})();(function(){google.sn='web';google.kHL='en';google.rdn=false;})();(function(){
var g=this||self;function k(){return window.google&&window.google.kOPI||null};var l,m=[];function n(a){for(var b;a&&(!a.getAttribute||!(b=a.getAttribute("eid")));)a=a.parentNode;return b||l}function p(a){for(var b=null;a&&(!a.getAttribute||!(b=a.getAttribute("leid")));)a=a.parentNode;return b}function q(a){/^http:/i.test(a)&&window.location.protocol==="https:"&&(google.ml&&google.ml(Error("a"),!1,{src:a,glmm:1}),a="");return a}
function r(a,b,d,c,h){var e="";b.search("&ei=")===-1&&(e="&ei="+n(c),b.search("&lei=")===-1&&(c=p(c))&&(e+="&lei="+c));var f=b.search("&cshid=")===-1&&a!=="slh";c="&zx="+Date.now().toString();g._cshid&&f&&(c+="&cshid="+g._cshid);(d=d())&&(c+="&opi="+d);return"/"+(h||"gen_204")+"?atyp=i&ct="+String(a)+"&cad="+(b+e+c)};l=google.kEI;google.getEI=n;google.getLEI=p;google.ml=function(){return null};google.log=function(a,b,d,c,h,e){e=e===void 0?k:e;d||(d=r(a,b,e,c,h));if(d=q(d)){a=new Image;var f=m.length;m[f]=a;a.onerror=a.onload=a.onabort=function(){delete m[f]};a.src=d}};google.logUrl=function(a,b){b=b===void 0?k:b;return r("",a,b)};}).call(this);(function(){google.y={};google.sy={};function e(a,b,c){if(a)var d=a.id;else{do d=Math.random();while(c[d])}c[d]=[a,b]}var f;(f=google).x||(f.x=function(a,b){e(a,b,google.y)});var g;(g=google).sx||(g.sx=function(a,b){e(a,b,google.sy)});google.lm=[];var h;(h=google).plm||(h.plm=function(a){google.lm.push.apply(google.lm,a)});google.lq=[];var k;(k=google).load||(k.load=function(a,b,c){google.lq.push([[a],b,c])});var l;(l=google).loadAll||(l.loadAll=function(a,b){google.lq.push([a,b])});google.bx=!1;var m;(m=google).lx||(m.lx=function(){});var n=[],p;(p=google).fce||(p.fce=function(a,b,c,d){n.push([a,b,c,d])});google.qce=n;google.adl=[];}).call(this);google.f={};(function(){
document.documentElement.addEventListener("submit",function(b){var a;if(a=b.target){var c=a.getAttribute("data-submitfalse");a=c==="1"||c==="q"&&!a.elements.q.value?!0:!1}else a=!1;a&&(b.preventDefault(),b.stopPropagation())},!0);document.documentElement.addEventListener("click",function(b){var a;a:{for(a=b.target;a&&a!==document.documentElement;a=a.parentElement)if(a.tagName==="A"){a=a.getAttribute("data-nohref")==="1";break a}a=!1}a&&b.preventDefault()},!0);}).call(this);(function(){google.hs={h:true,nhs:false,sie:false};})();(function(){google.c={cap:2000,doiu:1,timl:false,vis:true};})();(function(){
var n=this||self;window.google=window.google||{};var p=window.performance&&window.performance.timing&&"navigationStart"in window.performance.timing,aa=google.stvsc&&google.stvsc.ns,r=p?aa||window.performance.timing.navigationStart:void 0;function u(){return window.performance.now()-(google.stvsc&&google.stvsc.pno||0)}var ba=google.stvsc&&google.stvsc.rs,v=p?ba||window.performance.timing.responseStart:void 0;var ca=google.c.cap,da=window.google&&google.c&&google.c.cfc,ea=window.google&&google.c&&google.c.csnc,w=google.c.rv,fa=google.c.rvcf,x=google.c.timl;function y(a,b,d){google.tick("load",a,b,d)}function z(a,b){google.c.e("load",a,String(b))};var ha=function(a){this.g=a;this.v=[];var b=this.g.getAttribute("data-deferred");this.C=a.hasAttribute("data-noaft");this.i=!!b;if(b=!this.i)a:{for(b=0;b<A.length;++b)if(a.getAttribute("data-"+A[b])){b=!0;break a}b=!1}this.l=b;(b=a.src)&&this.l&&(this.D=b);!this.l&&b||a.setAttribute("data-lzy_","1");(this.j=this.C?!0:this.i||this.l?!1:!this.g.src||this.g.complete)||B(this);google.c.wh>1&&C(this)},B=function(a){google.rll(a.g,!0,function(){var b=Date.now();if(a.D&&a.g.src===a.D||a.g.getAttribute("data-deferred")===
"1")B(a);else if(!a.A){a.i&&a.g.setAttribute("data-deferred","3");a.A=b;a.g.setAttribute("data-iml",String(b));for(var d=0;d<a.v.length;++d)a.v[d](b);a.v.length=0}})},C=function(a,b){if(b||a.B===void 0)a.B=google.cv(a.g),a.g.setAttribute("data-atf",String(a.B));return a.B},ia=function(a,b){a.A||a.j?b(a.A||0):a.v.push(b)},A="src bsrc url ll image img-url lioi".split(" ");google.c.iim=google.c.iim||{};var D=google.c.iim,ja=0;function E(a){var b=a.getAttribute("data-csiid")||google.kEI+"_"+String(++ja);D[b]||(a.setAttribute("data-csiid",b),D[b]=new ha(a));return D[b]}function F(a,b){b=(b||document).getElementsByTagName("img");for(var d=0,c=b.length;d<c;++d)a(E(b[d]))};var G={};function H(a,b){google.timers.load.m[a]===!1?b():(G[a]||(G[a]=[]),G[a].push(b))}google.c.q=H;google.caft=function(a){H("aft",a)};function I(a,b,d){var c=da;var e=a.parentElement;if(e&&(e.classList.contains("q1MG4e")||e.classList.contains("uhHOwf"))&&(e.style.height||e.style.width)){var k=e.getBoundingClientRect(),h=a.getBoundingClientRect();if(k.height<h.height||k.width<h.width)a=e}if(!d){for(c=a;c&&c.id!=="center_col"&&c.id!=="rhs";)c=c.parentElement;d=c;c=!d}if(c||!d){for(c=a;c&&c!==d&&c.tagName!=="G-SCROLLING-CAROUSEL"&&(!ea||!c.hasAttribute("data-sn-container"));)c=c.parentElement;d=c}c=a;(a=!c)||(c.style.display==="none"?a=!0:document.defaultView&&document.defaultView.getComputedStyle?(a=document.defaultView.getComputedStyle(c),a=!!a&&(a.visibility==="hidden"||a.height==="0px"&&a.width==="0px")):a=!1);if(a)b=0;else if(c.getBoundingClientRect){b:{for(a=c;a&&a!==d;a=a.parentElement)if(a.style.overflow==="hidden")break b;a=null}(e=a)?(a=c.getBoundingClientRect(),e=e.getBoundingClientRect(),a=a.bottom<e.top||a.top>=e.bottom||a.right<e.left||a.left>=e.right):a=!1;if(a)b=0;else{a=c.getBoundingClientRect();var l=a.left+
(b?0:window.pageXOffset);e=a.top+(b?0:window.pageYOffset);k=a.width;h=a.height;var g=0;if(!(h<=0&&k<=0)){var m=window.innerHeight||document.documentElement.clientHeight;e+h<0?g=2:e>=m&&(g=4);if(l+k<0||l>=(window.innerWidth||document.documentElement.clientWidth))g|=8;else if(d){l=a.left;if(!b)for(b=c;b&&b!==d;b=b.parentElement)l+=b.scrollLeft;b=d.getBoundingClientRect();if(l+k<b.left||l>=b.right)g|=8;a.top>=b.bottom&&(g|=4)}g||(g=1,e+h>m&&(g|=4))}b=g}}else b=1;return b};google.timers={};google.startTick=function(a,b){google.timers[a]={t:{start:b||Date.now()},e:{},m:{}}};google.tick=function(a,b,d,c){d=d!==void 0?d:Date.now();google.timers[a].t[b]=d;c&&r&&performance.mark&&(a=d-r,a>0&&performance.mark(c,{startTime:a}))};google.c.e=function(a,b,d){google.timers[a].e[b]=d};google.c.b=function(a){var b=google.timers.load.m;b[a]&&google.ml(Error("b"),!1,{m:a});b[a]=!0};google.c.u=function(a){var b=google.timers.load.m,d=!0;if(b[a]){for(var c=G[a]||[],e=0;e<c.length;++e)try{c[e]()}catch(h){google.ml(h,!1)}c.length=0;b[a]=!1;for(var k in b)b[k]&&(d=!1)}else{d="";for(c in b)d+=c+":"+b[c]+";";google.ml(Error("a"),!1,{m:a,s:d});d=!1}(a=d)&&google.csiReport(google.timers.load,"all");return a};google.rll=function(a,b,d){function c(e){d(e);a.removeEventListener("load",c,!1);a.removeEventListener("error",c,!1)}a.addEventListener("load",c,!1);b&&a.addEventListener("error",c,!1)};var J,K=Date.now(),L=window.performance;L&&(L.now&&(J=Math.floor(u())),r&&v&&v>r&&v<=K&&(K=v,J=v-r));google.startTick("load",K);var M=J;google.timers.load.wsrt=M;performance.mark&&performance.mark("SearchAFTStart",{startTime:M});y("hst",window._hst,"SearchHeadStart");google.c.b("xe");function N(a){return document.visibilityState==="hidden"?(y("fht",a),!0):!1}function O(){N()&&P()}function P(){document.removeEventListener("visibilitychange",O,!0)}N(0)||document.addEventListener("visibilitychange",O,!0);google.c.rq=[P];google.cv=I;function Q(){var a,b;return(a=window.performance)==null?void 0:(b=a.getEntriesByType)==null?void 0:b.call(a,"navigation")[0]};function R(){var a;if((a=window.google)==null?0:a.rdn)return Q()}function S(){var a,b;return(a=window.performance)==null?void 0:(b=a.navigation)==null?void 0:b.type};var ka=window.location;function T(a){return(a=ka.search.match(new RegExp("[?&]"+a+"=(\\d+)\\b")))?Number(a[1]):-1}
function U(a){var b=google.timers.load,d=b.e,c=google.stvsc;c&&(d.ssr=1);c?c=c.isBF:c=(c=R())?c.type==="back_forward"?c.notRestoredReasons===void 0?!0:!!c.notRestoredReasons:!1:S()===2;c&&(d.bb=1);((c=R())?c.type==="reload":S()===1)&&(d.r=1);if(c=Q()){var e=c.type;e&&(d.nt=e);e=c.deliveryType;e!=null&&(d.dt=e);e=c.transferSize;e!=null&&(d.ts=e);c=c.nextHopProtocol;c!=null&&(d.nhp=c)}(c=window.navigation)&&(c=c.activation)&&(c=c.navigationType)&&(d.ant=c);d=b.m;if(!d||!d.prs){c=window._csc==="agsa"&&
window._cshid;e=!!google.stvsc;d=T("qsubts");e||((e=R())?(e=e.type,e=!e||e==="navigate"):e=!S(),e=!e);e=e||c?0:b.qsubts||d;var k="r";e>0&&(c=b.fbts||T("fbts"),c>0&&(b.t.start=Math.max(e,c),k=b.fbts===c?"i":"u"));var h=b.t,l=h.start;c={};b.wsrt!==void 0&&(c.wsrt=b.wsrt);if(l)for(var g in h)if(g!=="start"){var m=h[g];c[g]=g==="sgl"?m:g==="prs"?l-m:Math.max(m-l,0)}e>0&&(c.gsasrt=b.t.start-e,g=T("qsd"),g>0&&z("qsd",g),z("ests",(b.qsubts===e?"i":"u")+k),b.qsubts&&b.qsubts!==d&&z("qd",b.qsubts-d));b=b.e;a="/gen_204?s="+google.sn+"&t="+a+"&atyp=csi&ei="+google.kEI+"&rt=";g="";for(f in c)a+=""+g+f+"."+c[f],g=",";for(var q in b)a+="&"+q+"="+b[q];var f="";n._cshid&&(f+="&cshid="+n._cshid);(q=window.google&&window.google.kOPI||null)&&(f+="&opi="+q);f=a+=f;typeof navigator.sendBeacon==="function"?navigator.sendBeacon(f,""):google.log("","",f)}};function la(){y("cbt");U("cap")};function V(a,b,d,c){function e(m){++h;ia(m,function(q){if(c==null||c(m))g=Math.max(g,q);++l;k||h!==l||d(g)})}var k=!0,h=0,l=0,g=0;F(function(m){a(m)&&e(m)});b();(k=!1,h!==l)||d(g)};var ma=!1,W=0,X=0,Y=0,Z;function na(){Z&&clearTimeout(Z)}
function oa(a,b){function d(){z("ima",h);z("imad",l);z("imac",g)}google.c.wh>1||(google.c.wh=Math.floor(window.innerHeight||document.documentElement.clientHeight));var c=google.c.wh;var e=!b,k=!Y&&document.getElementById("rhs");b=b?Math.floor(b.getBoundingClientRect().top+window.pageYOffset):-1;k&&!e?(Y=a,F(function(f){f.F=!0},k)):(k=e||google.c.wh>1&&b>=c,!X&&k&&(X=a,W=b));if(e&&X){var h=0,l=0,g=0,m=!1,q=!1;V(function(f){if(!(C(f)&1))return!1;if(f.j)return++g,!f.C;C(f)&4&&(f.F?q=!0:m=!0);f.i&&++l;++h;return!0},function(){d();document.getElementsByClassName("Ib7Efc").length&&z("ddl",1);var f=document.getElementById("eKIzJc");f&&(f=I(f),z("aio",f));z("wh",c)},function(f){w&&d();f&&y("afti",f);W>0&&y("afts",X);Y&&y("aftr",Y);var t=X;Y>t&&(t=Y);f&&(f>t||m&&(!Y||W<0)||q&&W>0)&&(t=f);y("aft",t,"trigger:SearchAFTEnd");google.c.q("frt",function(){na();U("aft")});google.c.u("aft")},function(f){if(w){if(C(f,!0)&1)return!0;f.j?--g:(f.i&&--l,--h);return!1}if(fa){var t=google.cv(f.g);t&1||f.g.setAttribute("data-rvcf",String(t))}return!0})}};function pa(a){V(function(b){return!!(C(b)&1)},function(){y("frts",a)},function(b){y("frvt",Math.max(b,a));google.c.u("frt")})};var qa=!1;google.c.wh=Math.floor(window.innerHeight||document.documentElement.clientHeight);google.c.b("prt");var ra=ca||0;if(ra>0){a:{if(r!==void 0){var sa=ra-u();if(sa>0){Z=setTimeout(la,sa);break a}la()}Z=void 0}google.c.rq.push(na)}google.c.maft=function(a,b){F(function(){});ma||(google.c.b("aft"),ma=!0);oa(a,b)};google.c.mfrvt=function(a){pa(a)};google.c.miml=function(a){function b(c){C(c);return x&&!c.C&&(!c.l||!!(C(c)&1))}function d(c){x&&y("iml",c||a);google.c.u("iml")}qa||(google.c.b("iml"),function(){V(b,function(){},d)}(0),qa=!0)};google.c.b("frt");google.c.ubf=!0;google.c.setup=function(a){a=E(a);return google.c.wh>1?C(a):null};}).call(this);(function(){function b(){for(var a=google.drc.shift();a;)a(),a=google.drc.shift()};google.drc=[function(){google.tick&&google.tick("load","dcl")}];google.dclc=function(a){google.drc.length?google.drc.push(a):a()};window.addEventListener?(document.addEventListener("DOMContentLoaded",b,!1),window.addEventListener("load",b,!1)):window.attachEvent&&window.attachEvent("onload",b);}).call(this);(function(){
function e(c,d){for(var b=f,a=0;a<c.length;a++){var g=c[a];(d?b.etc:b.et).push(g);b.c.addEventListener(g,b.h,d)}};var f=function(){var c=window.document.documentElement,d=[],b=function(a){d.push(a)};return{c:c,q:d,et:[],etc:[],d:b,h:function(a){b({eventType:a.type,event:a,targetElement:a.target,eic:c,timeStamp:Date.now(),eia:void 0,eirp:void 0,eiack:void 0})}}}();e("click focusin focusout auxclick change copy dblclick beforeinput input keyup keydown keypress mousedown mouseenter mouseleave mousemove mouseout mouseover mouseup paste pointerdown pointerenter pointerleave pointerup touchstart touchmove touchend touchcancel transitioncancel transitionend transitionrun transitionstart animationcancel animationend dragover dragenter dragleave drop dragstart dragend scroll speech".split(" "));e(["focus","blur","error","load"],!0);window._ejsa=f;}).call(this);(function(){window.google.erd={jsr:1,bv:2330,sd:true,de:true,dpf:'QozV2xEUZfy7V250dVA7MTlX95upGBIdwZ9nKYpZpB8'};})();(function(){var sdo=false;var mei=10;var diel=0;
var g=this||self;var k,l=(k=g.mei)!=null?k:1,m,p=(m=g.diel)!=null?m:0,q,r=(q=g.sdo)!=null?q:!0,t=0,u,w=google.erd,x=w.jsr;google.ml=function(a,b,d,n,e){e=e===void 0?2:e;b&&(u=a&&a.message);d===void 0&&(d={});d.cad="ple_"+google.ple+".aple_"+google.aple;if(google.dl)return google.dl(a,e,d,!0),null;b=d;if(x<0){window.console&&console.error(a,b);if(x===-2)throw a;b=!1}else b=!a||!a.message||a.message==="Error loading script"||t>=l&&!n?!1:!0;if(!b)return null;t++;d=d||{};b=encodeURIComponent;var c="/gen_204?atyp=i&ei="+b(google.kEI);google.kEXPI&&(c+="&jexpid="+b(google.kEXPI));c+="&srcpg="+b(google.sn)+"&jsr="+b(w.jsr)+
"&bver="+b(w.bv);w.dpf&&(c+="&dpf="+b(w.dpf));var f=a.lineNumber;f!==void 0&&(c+="&line="+f);var h=a.fileName;h&&(h.indexOf("-extension:/")>0&&(e=3),c+="&script="+b(h),f&&h===window.location.href&&(f=document.documentElement.outerHTML.split("\n")[f],c+="&cad="+b(f?f.substring(0,300):"No script found.")));google.ple&&google.ple===1&&(e=2);c+="&jsel="+e;for(var v in d)c+="&",c+=b(v),c+="=",c+=b(d[v]);c=c+"&emsg="+b(a.name+": "+a.message);c=c+"&jsst="+b(a.stack||"N/A");c.length>=12288&&(c=c.substring(0,12288));a=c;n||google.log(0,"",a);return a};window.onerror=function(a,b,d,n,e){u!==a&&(a=e instanceof Error?e:Error(a),d===void 0||"lineNumber"in a||(a.lineNumber=d),b===void 0||"fileName"in a||(a.fileName=b),google.ml(a,!1,void 0,!1,a.name==="SyntaxError"||a.message.substring(0,11)==="SyntaxError"||a.message.indexOf("Script error")!==-1?3:p));u=null;r&&t>=l&&(window.onerror=null)};})();(function(){history.replaceState(history.state,"",function(a,b){return b.replace(new RegExp("(\\?|&)"+a+"=[^&#]*(&?)"),function(e,c,d){return d?c:""})}("sg_ss",location.href));}).call(this);google.arwt=function(a){a.href=document.getElementById(a.id.substring(a.id.slice(0,3)==="vcs"?3:1)).href;return!0};(function(){google.eufsv=true;(function(){var e=function(){for(var a=Number(this),c=[],b=a;b<arguments.length;b++)c[b-a]=arguments[b];return c};function g(a){var c=e.apply(1,arguments).filter(Boolean).join("&");if(!c)return a;var b=a.match(/[?&]adurl=/);return b?a.slice(0,b.index+1)+c+"&"+a.slice(b.index+1):a+(a.indexOf("?")<0?"?":"&")+c}function h(a,c){return a===0?"ri=1":a===1?c?"ri=24":"ri=27":a===2?c?"ri=25":"ri=26":""}function k(a,c){return c?"&"+a+"="+encodeURIComponent(c):""}
var l=function(a){var c=a.url;a=a.A;this.i=c;this.B=a;this.v=(new Date).getTime()-17040672E5;this.g={};for(var b=/[?&]([^&=]+)=([^&]*)/g;a=b.exec(c);)this.g[a[1]]=a[2]},m=function(a,c){return a.g[c]},p=function(a,c){if(a.g.dsh==="1")return null;var b=a.g.ae;if(b==="1"){var d=a.g.adurl;if(d)try{return{version:3,l:decodeURIComponent(d),j:g(a.i,"act=1",h(c,!0),n(a))}}catch(f){}}return b==="2"?{version:4,l:g(a.i,"dct=1","suid="+a.v,h(c,!1)),j:g(a.i,"act=1",h(c,!0),"suid="+a.v)}:null},q=function(a,c){return c===
2?g(a.i,"ri=2"):c===0?g(a.i,"ri=16"):a.i},n=function(a){a=a.B;if(!a)return"";var c=k("uap",a.platform)+k("uapv",a.platformVersion)+k("uafv",a.uaFullVersion)+k("uaa",a.architecture)+k("uam",a.model)+k("uab",a.bitness);a.fullVersionList&&(c+="&uafvl="+encodeURIComponent(a.fullVersionList.map(function(b){return encodeURIComponent(b.brand)+";"+encodeURIComponent(b.version)}).join("|")));a.wow64!=null&&(c+="&uaw="+Number(a.wow64));return c.slice(1)};
var r=/^\s*(?!javascript:)(?:[\w+.-]+:|[^:/?#]*(?:[/?#]|$))/i;var t=function(){var a=google.eufsv,c=this;this.g=null;(a===void 0?0:a)&&navigator.userAgentData&&navigator.userAgentData.getHighEntropyValues&&navigator.userAgentData.getHighEntropyValues("platform platformVersion uaFullVersion architecture model bitness fullVersionList wow64".split(" ")).then(function(b){c.g=b})};t.prototype.handle=function(a){var c=a.hasAttribute("data-ohref"),b=c?a.getAttribute("data-ohref"):a.href;c||a.setAttribute("data-ohref",b);c=m(new l({url:b}),"ch")===void 0?g(b,"ch=1"):b;b=new l({url:c,A:this.g});a:{var d=b.g.co;if(d==="1")d="https://www.googleadservices.com/pagead/conversion/16521530460/?gad_source=1&adview_type=3";else if(d==="2")d="https://www.google.com/pagead/1p-conversion/16521530460/?gad_source=1&adview_type=5";else break a;var f=b.g.gclid;f&&(d+="&adview_gclid="+f);navigator.sendBeacon(d,"")||v(d,!1)}a:{d=b.g.cce;if(d==="1")d=0;else if(d==="2")d=1;else{d=null;break a}f=g(b.i,"cc=1");var u=f.indexOf("?");d=u<0?null:{url:"https://www.googleadservices.com/pagead/aclk"+f.slice(u),method:d}}d&&(d.method===0?navigator.sendBeacon&&navigator.sendBeacon(d.url,""):d.method===1&&v(d.url,!0));w()&&b.g.ase==="5"?(b=p(b,2))?(a.attributionSrc=b.j,b=b.l):b="":b="";b||(b=this.g,b=new l({url:c,A:b===void 0?null:b}),b.g.dsh==="1"||b.g.aspm!=="1"?b=(d=p(b,0))?navigator.sendBeacon?navigator.sendBeacon(d.j,"")?d.l:q(b,2):q(b,0):c:(b=p(b,1))?(v(b.j,!0),b=b.l):b=c);b&&b!==a.href&&(c=b,r.test(c)&&(a.href=c))};function v(a,c){var b={keepalive:!0,mode:"no-cors"};c&&(b.credentials="include");fetch(a,b)}function x(a,c){var b=m(new l({url:a}),"nis");return b===c?a:b!==void 0?a.replace(/([?&])nis=[^&]*/,function(d,f){return f+"nis="+c}):g(a,"nis="+c)}function w(){var a;return!((a=document.featurePolicy)==null||!a.allowsFeature("attribution-reporting"))};var y=new t;google.ausb=function(a){if(!a)return google.ml(Error("a"),!1),!0;if(a.hasAttribute("data-impdclcc"))try{var c=a.hasAttribute("attributionsourceid")&&a.hasAttribute("attributiondestination")?"2":a.hasAttribute("attributionsrc")?w()?"6":"5":w()?"7":"8";var b=x(a.href,c);r.test(b)&&(a.href=b)}catch(d){}a.getAttribute("data-sbv2")&&y.handle(a);return!0};}).call(this);})();(function(){
var c=this||self;function d(a){return a?a.closest("A"):null}function e(a){if(a=d(a.target))switch(a.getAttribute("data-agdh")){case "arwt":google.arwt(a);break;case "fvd3vc":c.J4LCUe(a);break;case "EdKoMd":(0,google.f.LmvwCb)(a)}return!0};window.document.documentElement.addEventListener("mousedown",e,!0);window.document.documentElement.addEventListener("touchstart",e,!0);window.document.documentElement.addEventListener("click",function(a){var b=d(a.target);if(b)switch(b.getAttribute("data-agch")){case "ausb":google.ausb(b);break;case "HJ3bqe":window.YvikHb(a,b);break;case "cqUJI":(0,google.f.DfwaCb)(b)}return!0},!0);}).call(this);(function(){var t=2500;(function(){'use strict';function a(){const c=document.querySelectorAll("link[blocking=render]");for(const d of c)d.remove()}const b=t-performance.now();b>0?setTimeout(a,b):a();}).call(this);})();(function(){'use strict';
var h=this||self;const m=h.JSON.parse,q=h.JSON.stringify;function r(a,b,c){(a=a.getItem(b+";;"+c))?(b=a.indexOf("_"),a=b<0?null:m(a.substr(b+1))):a=null;return a}function t(a,b,c,d,e="m",n=!0){let k=!1,g;try{if(e!="x"){var f=a=="s"?window.sessionStorage:window.localStorage,l=r(f,"_c","i")||0,p=q(l+1);f.setItem("_c;;i","p:*|l:9007199254740991_"+p);g=l;p=f;f=b;l=c;var z=g,A=q(d);p.setItem(f+";;"+l,"p:"+e+"|l:"+(z+"_")+A);k=!0}}catch(D){}n&&(h.mPPkxd||(h.mPPkxd=[]),h.mPPkxd.push([k,arguments,g]))};var u=[{g:"data-vt-d",types:[]},{g:"data-vt-mb",types:["sb","mb"]},{g:"data-vt-rq",types:["rq"]},{g:"data-vt-spth",types:["spth"]},{g:"data-vt-lows",types:["lows"]}];function v(a,b,c){try{let d,e;a==null||(d=a.viewTransition)==null||(e=d.types)==null||e.clear();for(const n of b){let k,g,f;(k=a)==null||(g=k.viewTransition)==null||(f=g.types)==null||f.add(n)}}catch(d){google.ml(d,!0,{src:c})}}
function w(a){try{window.addEventListener("pageswap",b=>{v(b,a,"mpa_vt-ps");t("s","mpavt","mpa-vt-types",JSON.stringify(a))},{once:!0})}catch(b){google.ml(b,!0,{src:"mpa_vt-el"})}};let x;window.addEventListener("pagereveal",async a=>{a:{try{var b=r(window.sessionStorage,"mpavt","mpa-vt-types");break a}catch(c){}b=null}if(b){b=JSON.parse(b);try{window.sessionStorage.removeItem("mpavt;;mpa-vt-types")}catch(c){}b&&v(a,b,"mpa_vt-pr")}try{let c;await (a==null?void 0:(c=a.viewTransition)==null?void 0:c.finished)}finally{y()}},{once:!0});B();document.addEventListener("click",a=>{try{a:{for(const {g:c,types:d}of u){let e;if((e=a.target)==null?0:e.closest(`[${c}]`)){var b=d;break a}}b=[]}a=b;a.length>0?(B(),w(a)):y()}catch(c){google.ml(c,!0,{src:"mpa_vt-t"})}},{capture:!0,passive:!0});function C(){x||(x=document.createElement("style"),document.head.append(x));return x}function y(){C().textContent="@view-transition{navigation:none;}"}function B(){C().textContent="@view-transition{navigation:auto;}"};}).call(this);(function(){'use strict';try{window.addEventListener("pagereveal",async a=>{try{const c=a.viewTransition;if(c){await c.ready;a=[["root"],["sb"],["mb"],["ubi",!0]];for(const [l,d]of a)f(l,d)}}catch(c){google.ml(c,!0,{src:"mpa_vt-c"})}},{capture:!0,passive:!0})}catch(a){google.ml(a,!0,{src:"mpa_vt-i"})}function q(a){return Number(a.split("px")[0])}
function f(a,c){const l=`::view-transition-group(${a})`,d=document.getAnimations().find(r=>{let m;return((m=r.effect)==null?void 0:m.pseudoElement)===l});if(d){var n=d.effect,b=n.getKeyframes();if(b[1].width==="auto"){d.currentTime=d.effect.getTiming().duration;var e=window.getComputedStyle(document.documentElement,l);var g=new DOMMatrix(e.transform);var h=q(e.width);e=q(e.height);d.currentTime=0}else g=new DOMMatrix(b[1].transform),h=q(b[1].width),e=q(b[1].height);var k=new DOMMatrix(b[0].transform),p=q(b[0].height);h=q(b[0].width)/h;c=c?p/e:h;var t=k.e;k=k.f;var u=g.e;g=g.f;a!=="sb"&&(k+p<0||g+e<0)&&d.cancel();n.setKeyframes([{transform:`translate(${t}px, ${k}px) scale(${h}, ${c})`,easing:b[0].easing},{transform:`translate(${u}px, ${g}px) scale(1, 1)`,easing:b[1].easing}])}};}).call(this);`

**Path:** `HTML > HEAD`
**Details:**
  - before: `(function(){var l='th';var ei='D3kiaY7MAZyxqtsP0YGLwQg';var sr=10;(function(a,c,d){a="/gen_204?ei="+ei+"&sol="+a+"&atyp=i&sr="+(c===void 0?100:c);d&&(a+=d);if(navigator.sendBeacon!==void 0)navigator.sendBeacon(a);else{var b=new Image;b.onerror=b.onload=b.onabort=function(){b=null};b.src=a+"&sb=n&zx="+Date.now()}})(l,sr);})();`
  - after: `@view-transition{navigation:none;}`

*... and 92 more changes (see changes.json)*

## Change Types Explained

- `form_value_changed`: Input/textarea value changed
- `checkbox_state_changed`: Checkbox/radio checked state changed
- `option_selected_changed`: Select option selected state changed
- `node_added`: New element appeared in DOM
- `node_removed`: Element removed from DOM
- `text_changed`: Text content changed
- `attr_modified`: Attribute value changed
- `attr_added`: New attribute added
- `attr_removed`: Attribute removed
- `position_changed`: Element position/size changed
- `style_changed`: Computed styles changed

## Instructions

1. **Read the changes.json file** - This contains structured semantic changes
2. **Identify the specific changes** that indicate the objective was completed
3. **Generate JavaScript validation code** that:
   - Checks if the objective was completed successfully
   - **CRITICAL: DO NOT use `return` statements - end with a boolean expression**
   - Is based on ACTUAL observed changes (from changes.json)
   - Works in the browser context
   - Focuses on the most significant/reliable changes

## CRITICAL: Output Format

**DO NOT USE RETURN STATEMENTS!** The code is evaluated as an expression, not a function.

❌ WRONG:
```javascript
return document.querySelector('#success') !== null;
```

✅ CORRECT:
```javascript
// Check for the specific change
const element = document.querySelector('...');
element && element.value === 'expected'
```

The last line should be a boolean expression (no return keyword).

## Testing Your Code

**YOU MUST TEST YOUR CODE ON BOTH TABS** before declaring it complete.

**Endpoint:** POST http://localhost:8080/page/execute

**Browser State Information:**
- **Client ID:** 38ffd46f-8309-4218-87b5-9c0004975208
- **Tab ID (AFTER - task completed):** F021930B5F41405EFC4C77A24DC6B955
- **Tab ID (BEFORE - initial state):** 93CADF999486BF34D7641630B7091E1C

**Test 1: AFTER Tab (Should Return TRUE):**
```bash
curl -X POST http://localhost:8080/page/execute \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "38ffd46f-8309-4218-87b5-9c0004975208",
    "tabId": "F021930B5F41405EFC4C77A24DC6B955",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }'
```

**Expected Response:** `{"result": {"value": true}}`

**Test 2: BEFORE Tab (Should Return FALSE):**
```bash
curl -X POST http://localhost:8080/page/execute \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "38ffd46f-8309-4218-87b5-9c0004975208",
    "tabId": "93CADF999486BF34D7641630B7091E1C",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }'
```

**Expected Response:** `{"result": {"value": false}}`

**CRITICAL:** Your validation MUST:
- Return TRUE on the AFTER tab (task completed)
- Return FALSE on the BEFORE tab (task not done)
- This proves your validation correctly detects the change

**Error Response:**
```json
{
  "exceptionDetails": { "text": "Error message here" }
}
```

## Workflow

1. Read changes.json to understand what changed
2. Write validation code to: native/data/js-verifier/action/click/verify.js
3. Test it on the AFTER tab (should return TRUE)
4. Test it on the BEFORE tab (should return FALSE)
5. If you get errors or wrong results:
   - Read the existing native/data/js-verifier/action/click/verify.js
   - Identify the issue from the API error response
   - Edit and fix the file
   - Save the improved version
   - Test BOTH tabs again
6. Iterate until:
   - AFTER tab returns {"result": {"value": true}}
   - BEFORE tab returns {"result": {"value": false}}
7. Only then is your code complete

## Save Your Response
When you generate WORKING validation JavaScript (tested via API), save it to:
native/data/js-verifier/action/click/verify.js

The orchestrator will automatically pick it up and test it again for confirmation.

**IMPORTANT:** The file will NOT be deleted between iterations. You can read it,
learn from previous attempts, and improve it iteratively.
