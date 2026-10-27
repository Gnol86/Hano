var M=globalThis,I=M.ShadowRoot&&(M.ShadyCSS===void 0||M.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Z=Symbol(),fe=new WeakMap,T=class{constructor(i,e,t){if(this._$cssResult$=!0,t!==Z)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=i,this.t=e}get styleSheet(){let i=this.o,e=this.t;if(I&&i===void 0){let t=e!==void 0&&e.length===1;t&&(i=fe.get(e)),i===void 0&&((this.o=i=new CSSStyleSheet).replaceSync(this.cssText),t&&fe.set(e,i))}return i}toString(){return this.cssText}},ge=n=>new T(typeof n=="string"?n:n+"",void 0,Z),X=(n,...i)=>{let e=n.length===1?n[0]:i.reduce((t,s,o)=>t+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[o+1],n[0]);return new T(e,n,Z)},be=(n,i)=>{if(I)n.adoptedStyleSheets=i.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of i){let t=document.createElement("style"),s=M.litNonce;s!==void 0&&t.setAttribute("nonce",s),t.textContent=e.cssText,n.appendChild(t)}},ee=I?n=>n:n=>n instanceof CSSStyleSheet?(i=>{let e="";for(let t of i.cssRules)e+=t.cssText;return ge(e)})(n):n;var{is:Ge,defineProperty:Fe,getOwnPropertyDescriptor:Je,getOwnPropertyNames:Qe,getOwnPropertySymbols:Ye,getPrototypeOf:Ze}=Object,V=globalThis,$e=V.trustedTypes,Xe=$e?$e.emptyScript:"",et=V.reactiveElementPolyfillSupport,P=(n,i)=>n,te={toAttribute(n,i){switch(i){case Boolean:n=n?Xe:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,i){let e=n;switch(i){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},_e=(n,i)=>!Ge(n,i),ye={attribute:!0,type:String,converter:te,reflect:!1,useDefault:!1,hasChanged:_e};Symbol.metadata??=Symbol("metadata"),V.litPropertyMetadata??=new WeakMap;var b=class extends HTMLElement{static addInitializer(i){this._$Ei(),(this.l??=[]).push(i)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(i,e=ye){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(i)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(i,e),!e.noAccessor){let t=Symbol(),s=this.getPropertyDescriptor(i,t,e);s!==void 0&&Fe(this.prototype,i,s)}}static getPropertyDescriptor(i,e,t){let{get:s,set:o}=Je(this.prototype,i)??{get(){return this[e]},set(a){this[e]=a}};return{get:s,set(a){let c=s?.call(this);o?.call(this,a),this.requestUpdate(i,c,t)},configurable:!0,enumerable:!0}}static getPropertyOptions(i){return this.elementProperties.get(i)??ye}static _$Ei(){if(this.hasOwnProperty(P("elementProperties")))return;let i=Ze(this);i.finalize(),i.l!==void 0&&(this.l=[...i.l]),this.elementProperties=new Map(i.elementProperties)}static finalize(){if(this.hasOwnProperty(P("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(P("properties"))){let e=this.properties,t=[...Qe(e),...Ye(e)];for(let s of t)this.createProperty(s,e[s])}let i=this[Symbol.metadata];if(i!==null){let e=litPropertyMetadata.get(i);if(e!==void 0)for(let[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let s=this._$Eu(e,t);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(i){let e=[];if(Array.isArray(i)){let t=new Set(i.flat(1/0).reverse());for(let s of t)e.unshift(ee(s))}else i!==void 0&&e.push(ee(i));return e}static _$Eu(i,e){let t=e.attribute;return t===!1?void 0:typeof t=="string"?t:typeof i=="string"?i.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(i=>this.enableUpdating=i),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(i=>i(this))}addController(i){(this._$EO??=new Set).add(i),this.renderRoot!==void 0&&this.isConnected&&i.hostConnected?.()}removeController(i){this._$EO?.delete(i)}_$E_(){let i=new Map,e=this.constructor.elementProperties;for(let t of e.keys())this.hasOwnProperty(t)&&(i.set(t,this[t]),delete this[t]);i.size>0&&(this._$Ep=i)}createRenderRoot(){let i=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return be(i,this.constructor.elementStyles),i}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(i=>i.hostConnected?.())}enableUpdating(i){}disconnectedCallback(){this._$EO?.forEach(i=>i.hostDisconnected?.())}attributeChangedCallback(i,e,t){this._$AK(i,t)}_$ET(i,e){let t=this.constructor.elementProperties.get(i),s=this.constructor._$Eu(i,t);if(s!==void 0&&t.reflect===!0){let o=(t.converter?.toAttribute!==void 0?t.converter:te).toAttribute(e,t.type);this._$Em=i,o==null?this.removeAttribute(s):this.setAttribute(s,o),this._$Em=null}}_$AK(i,e){let t=this.constructor,s=t._$Eh.get(i);if(s!==void 0&&this._$Em!==s){let o=t.getPropertyOptions(s),a=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:te;this._$Em=s;let c=a.fromAttribute(e,o.type);this[s]=c??this._$Ej?.get(s)??c,this._$Em=null}}requestUpdate(i,e,t,s=!1,o){if(i!==void 0){let a=this.constructor;if(s===!1&&(o=this[i]),t??=a.getPropertyOptions(i),!((t.hasChanged??_e)(o,e)||t.useDefault&&t.reflect&&o===this._$Ej?.get(i)&&!this.hasAttribute(a._$Eu(i,t))))return;this.C(i,e,t)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(i,e,{useDefault:t,reflect:s,wrapped:o},a){t&&!(this._$Ej??=new Map).has(i)&&(this._$Ej.set(i,a??e??this[i]),o!==!0||a!==void 0)||(this._$AL.has(i)||(this.hasUpdated||t||(e=void 0),this._$AL.set(i,e)),s===!0&&this._$Em!==i&&(this._$Eq??=new Set).add(i))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let i=this.scheduleUpdate();return i!=null&&await i,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,o]of this._$Ep)this[s]=o;this._$Ep=void 0}let t=this.constructor.elementProperties;if(t.size>0)for(let[s,o]of t){let{wrapped:a}=o,c=this[s];a!==!0||this._$AL.has(s)||c===void 0||this.C(s,void 0,o,c)}}let i=!1,e=this._$AL;try{i=this.shouldUpdate(e),i?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(t){throw i=!1,this._$EM(),t}i&&this._$AE(e)}willUpdate(i){}_$AE(i){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(i)),this.updated(i)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(i){return!0}update(i){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(i){}firstUpdated(i){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[P("elementProperties")]=new Map,b[P("finalized")]=new Map,et?.({ReactiveElement:b}),(V.reactiveElementVersions??=[]).push("2.1.2");var se=globalThis,xe=n=>n,j=se.trustedTypes,Ae=j?j.createPolicy("lit-html",{createHTML:n=>n}):void 0,ne="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,oe="?"+$,tt=`<${oe}>`,S=document,N=()=>S.createComment(""),D=n=>n===null||typeof n!="object"&&typeof n!="function",ae=Array.isArray,ke=n=>ae(n)||typeof n?.[Symbol.iterator]=="function",ie=`[ 	
\f\r]`,H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,we=/-->/g,Se=/>/g,A=RegExp(`>|${ie}(?:([^\\s"'>=/]+)(${ie}*=${ie}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ce=/'/g,Ee=/"/g,qe=/^(?:script|style|textarea|title)$/i,re=n=>(i,...e)=>({_$litType$:n,strings:i,values:e}),r=re(1),ut=re(2),ht=re(3),y=Symbol.for("lit-noChange"),d=Symbol.for("lit-nothing"),Re=new WeakMap,w=S.createTreeWalker(S,129);function Te(n,i){if(!ae(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ae!==void 0?Ae.createHTML(i):i}var Pe=(n,i)=>{let e=n.length-1,t=[],s,o=i===2?"<svg>":i===3?"<math>":"",a=H;for(let c=0;c<e;c++){let l=n[c],u,v,p=-1,m=0;for(;m<l.length&&(a.lastIndex=m,v=a.exec(l),v!==null);)m=a.lastIndex,a===H?v[1]==="!--"?a=we:v[1]!==void 0?a=Se:v[2]!==void 0?(qe.test(v[2])&&(s=RegExp("</"+v[2],"g")),a=A):v[3]!==void 0&&(a=A):a===A?v[0]===">"?(a=s??H,p=-1):v[1]===void 0?p=-2:(p=a.lastIndex-v[2].length,u=v[1],a=v[3]===void 0?A:v[3]==='"'?Ee:Ce):a===Ee||a===Ce?a=A:a===we||a===Se?a=H:(a=A,s=void 0);let h=a===A&&n[c+1].startsWith("/>")?" ":"";o+=a===H?l+tt:p>=0?(t.push(u),l.slice(0,p)+ne+l.slice(p)+$+h):l+$+(p===-2?c:h)}return[Te(n,o+(n[e]||"<?>")+(i===2?"</svg>":i===3?"</math>":"")),t]},L=class n{constructor({strings:i,_$litType$:e},t){let s;this.parts=[];let o=0,a=0,c=i.length-1,l=this.parts,[u,v]=Pe(i,e);if(this.el=n.createElement(u,t),w.currentNode=this.el.content,e===2||e===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(s=w.nextNode())!==null&&l.length<c;){if(s.nodeType===1){if(s.hasAttributes())for(let p of s.getAttributeNames())if(p.endsWith(ne)){let m=v[a++],h=s.getAttribute(p).split($),f=/([.?@])?(.*)/.exec(m);l.push({type:1,index:o,name:f[2],strings:h,ctor:f[1]==="."?z:f[1]==="?"?K:f[1]==="@"?W:E}),s.removeAttribute(p)}else p.startsWith($)&&(l.push({type:6,index:o}),s.removeAttribute(p));if(qe.test(s.tagName)){let p=s.textContent.split($),m=p.length-1;if(m>0){s.textContent=j?j.emptyScript:"";for(let h=0;h<m;h++)s.append(p[h],N()),w.nextNode(),l.push({type:2,index:++o});s.append(p[m],N())}}}else if(s.nodeType===8)if(s.data===oe)l.push({type:2,index:o});else{let p=-1;for(;(p=s.data.indexOf($,p+1))!==-1;)l.push({type:7,index:o}),p+=$.length-1}o++}}static createElement(i,e){let t=S.createElement("template");return t.innerHTML=i,t}};function C(n,i,e=n,t){if(i===y)return i;let s=t!==void 0?e._$Co?.[t]:e._$Cl,o=D(i)?void 0:i._$litDirective$;return s?.constructor!==o&&(s?._$AO?.(!1),o===void 0?s=void 0:(s=new o(n),s._$AT(n,e,t)),t!==void 0?(e._$Co??=[])[t]=s:e._$Cl=s),s!==void 0&&(i=C(n,s._$AS(n,i.values),s,t)),i}var B=class{constructor(i,e){this._$AV=[],this._$AN=void 0,this._$AD=i,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(i){let{el:{content:e},parts:t}=this._$AD,s=(i?.creationScope??S).importNode(e,!0);w.currentNode=s;let o=w.nextNode(),a=0,c=0,l=t[0];for(;l!==void 0;){if(a===l.index){let u;l.type===2?u=new k(o,o.nextSibling,this,i):l.type===1?u=new l.ctor(o,l.name,l.strings,this,i):l.type===6&&(u=new G(o,this,i)),this._$AV.push(u),l=t[++c]}a!==l?.index&&(o=w.nextNode(),a++)}return w.currentNode=S,s}p(i){let e=0;for(let t of this._$AV)t!==void 0&&(t.strings!==void 0?(t._$AI(i,t,e),e+=t.strings.length-2):t._$AI(i[e])),e++}},k=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(i,e,t,s){this.type=2,this._$AH=d,this._$AN=void 0,this._$AA=i,this._$AB=e,this._$AM=t,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let i=this._$AA.parentNode,e=this._$AM;return e!==void 0&&i?.nodeType===11&&(i=e.parentNode),i}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(i,e=this){i=C(this,i,e),D(i)?i===d||i==null||i===""?(this._$AH!==d&&this._$AR(),this._$AH=d):i!==this._$AH&&i!==y&&this._(i):i._$litType$!==void 0?this.$(i):i.nodeType!==void 0?this.T(i):ke(i)?this.k(i):this._(i)}O(i){return this._$AA.parentNode.insertBefore(i,this._$AB)}T(i){this._$AH!==i&&(this._$AR(),this._$AH=this.O(i))}_(i){this._$AH!==d&&D(this._$AH)?this._$AA.nextSibling.data=i:this.T(S.createTextNode(i)),this._$AH=i}$(i){let{values:e,_$litType$:t}=i,s=typeof t=="number"?this._$AC(i):(t.el===void 0&&(t.el=L.createElement(Te(t.h,t.h[0]),this.options)),t);if(this._$AH?._$AD===s)this._$AH.p(e);else{let o=new B(s,this),a=o.u(this.options);o.p(e),this.T(a),this._$AH=o}}_$AC(i){let e=Re.get(i.strings);return e===void 0&&Re.set(i.strings,e=new L(i)),e}k(i){ae(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,t,s=0;for(let o of i)s===e.length?e.push(t=new n(this.O(N()),this.O(N()),this,this.options)):t=e[s],t._$AI(o),s++;s<e.length&&(this._$AR(t&&t._$AB.nextSibling,s),e.length=s)}_$AR(i=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);i!==this._$AB;){let t=xe(i).nextSibling;xe(i).remove(),i=t}}setConnected(i){this._$AM===void 0&&(this._$Cv=i,this._$AP?.(i))}},E=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(i,e,t,s,o){this.type=1,this._$AH=d,this._$AN=void 0,this.element=i,this.name=e,this._$AM=s,this.options=o,t.length>2||t[0]!==""||t[1]!==""?(this._$AH=Array(t.length-1).fill(new String),this.strings=t):this._$AH=d}_$AI(i,e=this,t,s){let o=this.strings,a=!1;if(o===void 0)i=C(this,i,e,0),a=!D(i)||i!==this._$AH&&i!==y,a&&(this._$AH=i);else{let c=i,l,u;for(i=o[0],l=0;l<o.length-1;l++)u=C(this,c[t+l],e,l),u===y&&(u=this._$AH[l]),a||=!D(u)||u!==this._$AH[l],u===d?i=d:i!==d&&(i+=(u??"")+o[l+1]),this._$AH[l]=u}a&&!s&&this.j(i)}j(i){i===d?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,i??"")}},z=class extends E{constructor(){super(...arguments),this.type=3}j(i){this.element[this.name]=i===d?void 0:i}},K=class extends E{constructor(){super(...arguments),this.type=4}j(i){this.element.toggleAttribute(this.name,!!i&&i!==d)}},W=class extends E{constructor(i,e,t,s,o){super(i,e,t,s,o),this.type=5}_$AI(i,e=this){if((i=C(this,i,e,0)??d)===y)return;let t=this._$AH,s=i===d&&t!==d||i.capture!==t.capture||i.once!==t.once||i.passive!==t.passive,o=i!==d&&(t===d||s);s&&this.element.removeEventListener(this.name,this,t),o&&this.element.addEventListener(this.name,this,i),this._$AH=i}handleEvent(i){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,i):this._$AH.handleEvent(i)}},G=class{constructor(i,e,t){this.element=i,this.type=6,this._$AN=void 0,this._$AM=e,this.options=t}get _$AU(){return this._$AM._$AU}_$AI(i){C(this,i)}},He={M:ne,P:$,A:oe,C:1,L:Pe,R:B,D:ke,V:C,I:k,H:E,N:K,U:W,B:z,F:G},it=se.litHtmlPolyfillSupport;it?.(L,k),(se.litHtmlVersions??=[]).push("3.3.3");var Ne=(n,i,e)=>{let t=e?.renderBefore??i,s=t._$litPart$;if(s===void 0){let o=e?.renderBefore??null;t._$litPart$=s=new k(i.insertBefore(N(),o),o,void 0,e??{})}return s._$AI(n),s};var le=globalThis,_=class extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let i=super.createRenderRoot();return this.renderOptions.renderBefore??=i.firstChild,i}update(i){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(i),this._$Do=Ne(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return y}};_._$litElement$=!0,_.finalized=!0,le.litElementHydrateSupport?.({LitElement:_});var st=le.litElementPolyfillSupport;st?.({LitElement:_});(le.litElementVersions??=[]).push("4.2.2");var De={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},Le=n=>(...i)=>({_$litDirective$:n,values:i}),F=class{constructor(i){}get _$AU(){return this._$AM._$AU}_$AT(i,e,t){this._$Ct=i,this._$AM=e,this._$Ci=t}_$AS(i,e){return this.update(i,e)}update(i,e){return this.render(...e)}};var{I:nt}=He,Ue=n=>n;var Oe=()=>document.createComment(""),q=(n,i,e)=>{let t=n._$AA.parentNode,s=i===void 0?n._$AB:i._$AA;if(e===void 0){let o=t.insertBefore(Oe(),s),a=t.insertBefore(Oe(),s);e=new nt(o,a,n,n.options)}else{let o=e._$AB.nextSibling,a=e._$AM,c=a!==n;if(c){let l;e._$AQ?.(n),e._$AM=n,e._$AP!==void 0&&(l=n._$AU)!==a._$AU&&e._$AP(l)}if(o!==s||c){let l=e._$AA;for(;l!==o;){let u=Ue(l).nextSibling;Ue(t).insertBefore(l,s),l=u}}}return e},x=(n,i,e=n)=>(n._$AI(i,e),n),ot={},Me=(n,i=ot)=>n._$AH=i,Ie=n=>n._$AH,J=n=>{n._$AR(),n._$AA.remove()};var Ve=(n,i,e)=>{let t=new Map;for(let s=i;s<=e;s++)t.set(n[s],s);return t},U=Le(class extends F{constructor(n){if(super(n),n.type!==De.CHILD)throw Error("repeat() can only be used in text expressions")}dt(n,i,e){let t;e===void 0?e=i:i!==void 0&&(t=i);let s=[],o=[],a=0;for(let c of n)s[a]=t?t(c,a):a,o[a]=e(c,a),a++;return{values:o,keys:s}}render(n,i,e){return this.dt(n,i,e).values}update(n,[i,e,t]){let s=Ie(n),{values:o,keys:a}=this.dt(i,e,t);if(!Array.isArray(s))return this.ut=a,o;let c=this.ut??=[],l=[],u,v,p=0,m=s.length-1,h=0,f=o.length-1;for(;p<=m&&h<=f;)if(s[p]===null)p++;else if(s[m]===null)m--;else if(c[p]===a[h])l[h]=x(s[p],o[h]),p++,h++;else if(c[m]===a[f])l[f]=x(s[m],o[f]),m--,f--;else if(c[p]===a[f])l[f]=x(s[p],o[f]),q(n,l[f+1],s[p]),p++,f--;else if(c[m]===a[h])l[h]=x(s[m],o[h]),q(n,s[p],s[m]),m--,h++;else if(u===void 0&&(u=Ve(a,h,f),v=Ve(c,p,m)),u.has(c[p]))if(u.has(c[m])){let g=v.get(a[h]),Y=g!==void 0?s[g]:null;if(Y===null){let ve=q(n,s[p]);x(ve,o[h]),l[h]=ve}else l[h]=x(Y,o[h]),q(n,s[p],Y),s[g]=null;h++}else J(s[m]),m--;else J(s[p]),p++;for(;h<=f;){let g=q(n,l[f+1]);x(g,o[h]),l[h++]=g}for(;p<=m;){let g=s[p++];g!==null&&J(g)}return this.ut=a,Me(n,l),y}});var R=n=>structuredClone(n),je=()=>({persons:[],rooms:[],tts_entity_id:"",tts_language:"",history_days:30,native_volume_entity_ids:[]}),ce=()=>({notification_id:"",title:"",message:"",recipient_mode:"selected",person_entity_ids:[],notify_entity_ids:[],mobile_device_ids:[],channels:["mobile"],respect_sleep:!0,delivery:"immediate",priority:"normal",ios_sound:"",reminder_interval:0,reminder_limit:0,cycle_mode:"update",expires_in:0,resolve_on_clear:!1,image_url:"",click_url:"",camera_entity_id:"",icon:"",color:"",timeout:0,voice_mode:"explicit",media_player_entity_ids:[],tts_entity_id:"",tts_language:"",voice_message:"",volume:null,buttons:[]}),O=class{constructor(){this.value=je();this.base=je();this.revision=0;this.conflict=!1}get dirty(){return JSON.stringify(this.value)!==JSON.stringify(this.base)}reset(i,e){this.value=R(i),this.base=R(i),this.revision=e,this.conflict=!1}receive(i,e){e<this.revision||(this.dirty?e!==this.revision&&(this.conflict=!0):this.reset(i,e))}acknowledge(i,e,t){JSON.stringify(this.value)===JSON.stringify(i)&&(this.value=R(e)),this.base=R(e),this.revision=t,this.conflict=!1}},Be=(n,i)=>n.includes(i)?n.filter(e=>e!==i):[...n,i];function ze(n){return n?.code??"error"}function de(){if(typeof globalThis.crypto.randomUUID=="function")return globalThis.crypto.randomUUID();let n=globalThis.crypto.getRandomValues(new Uint8Array(16));n[6]=n[6]&15|64,n[8]=n[8]&63|128;let i=Array.from(n,e=>e.toString(16).padStart(2,"0"));return[i.slice(0,4).join(""),i.slice(4,6).join(""),i.slice(6,8).join(""),i.slice(8,10).join(""),i.slice(10).join("")].join("-")}var pe={voice_no_longer_eligible:["The speaker is no longer eligible for this announcement.","L\u2019enceinte n\u2019est plus disponible pour cette annonce selon les r\xE8gles de routage.","El altavoz ya no cumple las condiciones para este anuncio."],storage_error:["Notification state could not be saved. Check Home Assistant storage.","L\u2019\xE9tat de la notification n\u2019a pas pu \xEAtre enregistr\xE9. V\xE9rifie le stockage Home Assistant.","No se pudo guardar el estado de la notificaci\xF3n. Revisa el almacenamiento de Home Assistant."],invalid_target:["Check the selected people, notification devices, cameras, and TTS entities.","V\xE9rifie les personnes, appareils, cam\xE9ras et entit\xE9s TTS s\xE9lectionn\xE9s.","Revisa las personas, dispositivos, c\xE1maras y entidades TTS seleccionados."],unsupported_options:["A selected destination does not support this combination of options.","Une destination s\xE9lectionn\xE9e ne prend pas en charge cette combinaison d\u2019options.","Un destino seleccionado no admite esta combinaci\xF3n de opciones."],unsupported_volume:["Native volume requires an explicitly verified Sonos player.","Le volume natif n\xE9cessite un lecteur Sonos explicitement v\xE9rifi\xE9.","El volumen nativo requiere un reproductor Sonos verificado expl\xEDcitamente."],not_loaded:["Set up the Hano integration first.","Configure d\u2019abord l\u2019int\xE9gration Hano.","Configura primero la integraci\xF3n Hano."],not_found:["This notification no longer exists.","Cette notification n\u2019existe plus.","Esta notificaci\xF3n ya no existe."],unsupported:["Not supported","Non pris en charge","No compatible"],remote_clear_unsupported:["This provider cannot clear a notification remotely.","Ce fournisseur ne permet pas l\u2019effacement \xE0 distance.","Este proveedor no permite borrar notificaciones a distancia."],superseded:["Replaced by a new cycle","Remplac\xE9e par un nouveau cycle","Sustituida por un ciclo nuevo"],received:["Received by device","R\xE9ception signal\xE9e par l\u2019appareil","Recepci\xF3n confirmada por el dispositivo"],restart_no_replay:["No voice replay after restart","Aucun rejeu vocal apr\xE8s red\xE9marrage","Sin repetici\xF3n de voz tras reiniciar"],unknown_recipient:["Recipient unavailable","Destinataire indisponible","Destinatario no disponible"],transport_timeout:["Transport timed out; outcome unknown","D\xE9lai de transport d\xE9pass\xE9 ; r\xE9sultat inconnu","Tiempo de transporte agotado; resultado desconocido"],clear_timeout:["Clearing timed out; outcome unknown","D\xE9lai d\u2019effacement d\xE9pass\xE9 ; r\xE9sultat inconnu","Tiempo de borrado agotado; resultado desconocido"],mobile_clear:["Dismissed on mobile","Effac\xE9e sur le mobile","Descartada en el m\xF3vil"],room_unknown_sleep:["Room silence status unknown","\xC9tat de silence de la pi\xE8ce inconnu","Estado de silencio de la habitaci\xF3n desconocido"],invalid_home_position:["Home coordinates invalid","Coordonn\xE9es du domicile invalides","Coordenadas del hogar inv\xE1lidas"],activeSingle:["Active","Active","Activa"],persons:["People","Personnes","Personas"],person_id:["Person","Personne","Persona"],channel:["Channel","Canal","Canal"],status:["Status","\xC9tat","Estado"],routing:["Routing","Routage","Enrutamiento"],destinations:["Destinations","Destinations","Destinos"],reasons:["Routing notes","Motifs de routage","Notas de enrutamiento"],media_player_entity_ids:["Speakers","Enceintes","Altavoces"],distance:["Distance (m)","Distance (m)","Distancia (m)"],notification_id:["Notification ID","Identifiant de notification","ID de notificaci\xF3n"],cycle_id:["Cycle","Cycle","Ciclo"],key:["Destination ID","Identifiant de destination","ID de destino"],updated_at:["Updated","Actualis\xE9","Actualizado"],interrupted:["Send interrupted; outcome unknown","Envoi interrompu ; r\xE9sultat inconnu","Env\xEDo interrumpido; resultado desconocido"],button_completed:["Button actions completed","Actions du bouton termin\xE9es","Acciones del bot\xF3n completadas"],button_failed:["Button actions failed","\xC9chec des actions du bouton","Error en las acciones del bot\xF3n"],manual:["Manual resolution","R\xE9solution manuelle","Resoluci\xF3n manual"],button:["Button resolution","R\xE9solution par bouton","Resoluci\xF3n por bot\xF3n"],removed_in_home_assistant:["Dismissed in Home Assistant","Supprim\xE9e dans Home Assistant","Descartada en Home Assistant"],expires_reason:["Expired","Expir\xE9e","Caducada"],sleeping:["Asleep","Endormi","Dormido"],missing_position:["Location unavailable","Position indisponible","Ubicaci\xF3n no disponible"],invalid_position:["Invalid coordinates","Coordonn\xE9es invalides","Coordenadas inv\xE1lidas"],room_unoccupied:["Room unoccupied","Pi\xE8ce inoccup\xE9e","Habitaci\xF3n desocupada"],unknown_occupancy:["Occupancy unknown","Occupation inconnue","Ocupaci\xF3n desconocida"],room_sleeping:["Room in quiet mode","Pi\xE8ce en mode silence","Habitaci\xF3n en silencio"],unknown_room_sleep:["Room silence status unknown","\xC9tat de silence de la pi\xE8ce inconnu","Estado de silencio de la habitaci\xF3n desconocido"],clearing:["Clearing in progress","Effacement en cours","Borrado en curso"],notifications:["Notifications","Notifications","Notificaciones"],people:["People","Personnes","Personas"],rooms:["Rooms & voice","Pi\xE8ces et voix","Habitaciones y voz"],settings:["Tests & settings","Tests et r\xE9glages","Pruebas y ajustes"],menu:["Open Home Assistant menu","Ouvrir le menu Home Assistant","Abrir el men\xFA de Home Assistant"],loading:["Connecting to Hano\u2026","Connexion \xE0 Hano\u2026","Conectando a Hano\u2026"],retry:["Reconnect","Reconnecter","Reconectar"],forbidden:["Administrator access is required.","Un acc\xE8s administrateur est n\xE9cessaire.","Se requiere acceso de administrador."],error:["The operation failed. Try again.","L\u2019op\xE9ration a \xE9chou\xE9. R\xE9essaie.","La operaci\xF3n ha fallado. Vuelve a intentarlo."],invalid_config:["Check your configuration fields.","V\xE9rifie les champs de configuration.","Revisa los campos de configuraci\xF3n."],invalid_request:["Check the notification fields.","V\xE9rifie les champs de la notification.","Revisa los campos de la notificaci\xF3n."],conflict:["Configuration changed elsewhere. Your draft is preserved. Discard it to reload the current configuration.","La configuration a chang\xE9 ailleurs. Ton brouillon est conserv\xE9. Abandonne-le pour charger la configuration actuelle.","La configuraci\xF3n ha cambiado en otro lugar. Tu borrador se conserva. Desc\xE1rtalo para cargar la configuraci\xF3n actual."],revision_conflict:["Configuration changed elsewhere. Discard your draft to load the latest version.","La configuration a chang\xE9 ailleurs. Abandonne ton brouillon pour charger la derni\xE8re version.","La configuraci\xF3n ha cambiado en otro lugar. Descarta tu borrador para cargar la \xFAltima versi\xF3n."],save:["Save","Enregistrer","Guardar"],saving:["Saving\u2026","Enregistrement\u2026","Guardando\u2026"],discard:["Discard","Abandonner","Descartar"],unsaved:["Unsaved configuration changes","Modifications de configuration non enregistr\xE9es","Cambios de configuraci\xF3n sin guardar"],saved:["Configuration saved","Configuration enregistr\xE9e","Configuraci\xF3n guardada"],saveFirst:["Save or discard your configuration changes before running a test.","Enregistre ou abandonne tes modifications avant de lancer un test.","Guarda o descarta los cambios antes de ejecutar una prueba."],add:["Add","Ajouter","A\xF1adir"],remove:["Remove","Supprimer","Eliminar"],name:["Display name","Nom affich\xE9","Nombre visible"],none:["None","Aucun","Ninguno"],back:["Back to notifications","Retour aux notifications","Volver a notificaciones"],search:["Search notifications","Rechercher une notification","Buscar notificaciones"],active:["Active","Actives","Activas"],pending:["Waiting","En attente","En espera"],history:["History","Historique","Historial"],all:["All residents","Tous les r\xE9sidents","Todos los residentes"],noNotifications:["No notifications in this view","Aucune notification dans cette vue","No hay notificaciones en esta vista"],chooseNotification:["Choose a notification","Choisis une notification","Elige una notificaci\xF3n"],chooseHint:["Follow individual destinations, pending sends and resolutions.","Suis les destinataires, les envois en attente et les r\xE9solutions.","Sigue los destinos, los env\xEDos pendientes y las resoluciones."],resolve:["Resolve everywhere","R\xE9soudre partout","Resolver en todos los destinos"],resolved:["Resolved","R\xE9solue","Resuelta"],expired:["Expired","Expir\xE9e","Caducada"],accepted:["Call accepted","Appel accept\xE9","Llamada aceptada"],skipped:["Skipped","Ignor\xE9","Omitido"],failed:["Failed","\xC9chec","Error"],unknown:["Unknown","Inconnu","Desconocido"],cancelled:["Cancelled","Annul\xE9","Cancelado"],sending:["Sending","Envoi en cours","Enviando"],cleared:["Clearing confirmed","Effacement confirm\xE9","Borrado confirmado"],clear_requested:["Clearing requested","Effacement demand\xE9","Borrado solicitado"],uncertain:["Outcome unknown","R\xE9sultat inconnu","Resultado desconocido"],deliveries:["Destinations","Destinations","Destinos"],timeline:["Activity","Activit\xE9","Actividad"],created:["Created","Cr\xE9\xE9e","Creada"],updated:["Updated","Actualis\xE9e","Actualizada"],expires:["Expires","Expire","Caduca"],unlimited:["No expiration","Sans expiration","Sin caducidad"],cycle:["Cycle","Cycle","Ciclo"],evidence:["An accepted call does not confirm delivery or that someone read or heard the message.","Un appel accept\xE9 ne confirme ni la livraison, ni la lecture, ni l\u2019\xE9coute du message.","Una llamada aceptada no confirma la entrega, la lectura ni la escucha del mensaje."],noPeople:["Add residents to route notifications by presence and sleep.","Ajoute des r\xE9sidents pour tenir compte de la pr\xE9sence et du sommeil.","A\xF1ade residentes para tener en cuenta la presencia y el sue\xF1o."],addPerson:["Add a person","Ajouter une personne","A\xF1adir una persona"],person:["Person","Personne","Persona"],sleep:["Sleep sensor (on = asleep)","Capteur de sommeil (on = endormi)","Sensor de sue\xF1o (on = dormido)"],devices:["Notification devices","Appareils de notification","Dispositivos de notificaci\xF3n"],addDevice:["Add a device","Ajouter un appareil","A\xF1adir un dispositivo"],target:["Notification destination","Destination de notification","Destino de notificaci\xF3n"],type:["Adapter","Adaptateur","Adaptador"],mobile:["Mobile","Mobile","M\xF3vil"],notify:["Generic notify","Notify g\xE9n\xE9rique","Notify gen\xE9rico"],platform:["Platform","Plateforme","Plataforma"],ios:["iOS","iOS","iOS"],android:["Android","Android","Android"],generic:["Generic","G\xE9n\xE9rique","Gen\xE9rico"],deviceId:["Companion device ID","Identifiant d\u2019appareil Companion","ID de dispositivo Companion"],devicesHelp:["Choose a discovered Companion service to fill in the platform and device ID. Generic destinations support basic content only.","Choisis un service Companion d\xE9tect\xE9 pour remplir la plateforme et l\u2019identifiant de l\u2019appareil. Les destinations g\xE9n\xE9riques acceptent uniquement le contenu simple.","Elige un servicio Companion detectado para rellenar la plataforma y el ID. Los destinos gen\xE9ricos solo admiten contenido b\xE1sico."],addRoom:["Add a room","Ajouter une pi\xE8ce","A\xF1adir una habitaci\xF3n"],noRooms:["Add rooms to announce only where someone is present.","Ajoute des pi\xE8ces pour annoncer uniquement l\xE0 o\xF9 quelqu\u2019un est pr\xE9sent.","A\xF1ade habitaciones para anunciar solo donde haya alguien."],roomName:["Room name","Nom de la pi\xE8ce","Nombre de la habitaci\xF3n"],area:["Area","Zone","\xC1rea"],occupancy:["Occupancy sensor (on = occupied)","Capteur d\u2019occupation (on = occup\xE9)","Sensor de ocupaci\xF3n (on = ocupado)"],roomSleep:["Silence / sleep sensor (on = silent)","Capteur de silence / sommeil (on = silencieux)","Sensor de silencio / sue\xF1o (on = silencio)"],speakers:["Speakers","Enceintes","Altavoces"],voiceHelp:["Voice is immediate only. An announcement never marks a person as having received the notification.","La voix est imm\xE9diate uniquement. Une annonce ne marque jamais une personne comme ayant re\xE7u la notification.","La voz es inmediata. Un anuncio nunca marca a una persona como destinataria de una notificaci\xF3n recibida."],defaults:["Voice defaults","Valeurs vocales par d\xE9faut","Valores de voz predeterminados"],tts:["Text-to-speech engine","Moteur de synth\xE8se vocale","Motor de s\xEDntesis de voz"],language:["TTS language (optional)","Langue TTS (facultative)","Idioma TTS (opcional)"],nativeVolume:["Verified native announcement volume","Volume natif des annonces v\xE9rifi\xE9","Volumen nativo de anuncios verificado"],nativeVolumeHelp:["Select only compatible Sonos players whose native announcement volume you have verified. No temporary media volume changes are used.","S\xE9lectionne uniquement les lecteurs Sonos compatibles dont tu as v\xE9rifi\xE9 le volume natif des annonces. Aucun changement temporaire du volume multim\xE9dia n\u2019est utilis\xE9.","Selecciona solo reproductores Sonos compatibles cuyo volumen nativo de anuncios hayas verificado. No se cambia temporalmente el volumen multimedia."],retention:["History retention (days)","Conservation de l\u2019historique (jours)","Conservaci\xF3n del historial (d\xEDas)"],privacy:["History & privacy","Historique et confidentialit\xE9","Historial y privacidad"],privacyHelp:["History is available to administrators only. Active notifications are retained until resolved.","L\u2019historique est r\xE9serv\xE9 aux administrateurs. Les notifications actives sont conserv\xE9es jusqu\u2019\xE0 leur r\xE9solution.","El historial solo est\xE1 disponible para administradores. Las notificaciones activas se conservan hasta su resoluci\xF3n."],purge:["Purge completed history","Purger l\u2019historique termin\xE9","Borrar historial completado"],confirmPurge:["Delete the history of all resolved and expired notifications? Active notifications will remain.","Supprimer l\u2019historique de toutes les notifications r\xE9solues et expir\xE9es ? Les notifications actives seront conserv\xE9es.","\xBFEliminar el historial de todas las notificaciones resueltas y caducadas? Las activas se conservar\xE1n."],purged:["Completed history removed","Historique termin\xE9 supprim\xE9","Historial completado eliminado"],tests:["Try a notification","Essayer une notification","Probar una notificaci\xF3n"],testHelp:["Preview calculates routing without sending. Send test performs real calls on the selected destinations.","La simulation calcule le routage sans envoyer. Le test r\xE9el appelle les destinations s\xE9lectionn\xE9es.","La vista previa calcula el enrutamiento sin enviar. La prueba real llama a los destinos seleccionados."],preview:["Preview without sending","Simuler sans envoyer","Vista previa sin enviar"],send:["Send real test","Envoyer un test r\xE9el","Enviar prueba real"],result:["Result","R\xE9sultat","Resultado"],id:["Notification ID (optional)","Identifiant de notification (facultatif)","ID de notificaci\xF3n (opcional)"],title:["Title","Titre","T\xEDtulo"],message:["Message","Message","Mensaje"],recipients:["Recipients","Destinataires","Destinatarios"],selected:["Selected people","Personnes s\xE9lectionn\xE9es","Personas seleccionadas"],present:["Present residents","R\xE9sidents pr\xE9sents","Residentes presentes"],absent:["Absent residents","R\xE9sidents absents","Residentes ausentes"],nearest:["Nearest residents","R\xE9sidents les plus proches","Residentes m\xE1s cercanos"],nearestHelp:["Uses person coordinates and the home location. No proximity entity is needed. Ties are included.","Utilise les coordonn\xE9es des personnes et la position du domicile. Aucune entit\xE9 proximity n\xE9cessaire. Les ex \xE6quo sont inclus.","Usa las coordenadas de las personas y la ubicaci\xF3n del hogar. No necesita entidades proximity. Incluye los empates."],directDevices:["Direct Companion devices","Appareils Companion directs","Dispositivos Companion directos"],directNotify:["Direct notify entities","Entit\xE9s notify directes","Entidades notify directas"],channels:["Channels","Canaux","Canales"],voice:["Voice","Voix","Voz"],persistent:["Home Assistant persistent notification","Notification persistante Home Assistant","Notificaci\xF3n persistente de Home Assistant"],respectSleep:["Respect sleep","Respecter le sommeil","Respetar el sue\xF1o"],delivery:["Availability","Disponibilit\xE9","Disponibilidad"],immediate:["Eligible now only","\xC9ligibles maintenant uniquement","Solo disponibles ahora"],when_available:["Wait individually until available","Attendre individuellement la disponibilit\xE9","Esperar individualmente hasta la disponibilidad"],priority:["Mobile priority","Priorit\xE9 mobile","Prioridad m\xF3vil"],reminderInterval:["Reminder interval (seconds, 0 = off)","Intervalle des rappels (secondes, 0 = d\xE9sactiv\xE9)","Intervalo de recordatorios (segundos, 0 = desactivado)"],reminderLimit:["Maximum reminders per destination (0 = off)","Nombre maximal de rappels par destination (0 = d\xE9sactiv\xE9)","M\xE1ximo de recordatorios por destino (0 = desactivado)"],reminderHelp:["Leave both at 0 to disable. Otherwise choose 60\u201386400 seconds and 1\u2013100 reminders, and add an acknowledgement button with Resolve enabled and no actions. One person's acknowledgement stops the cycle for everyone. Reading/opening is not reliably reported. Mobile only; sleep and presence still apply. No voice replay or catch-up after restart. Updates keep the count and restart the interval.","Laisse les deux \xE0 0 pour d\xE9sactiver. Sinon, choisis 60\u201386400 secondes et 1\u2013100 rappels, et ajoute un bouton d\u2019acquittement avec R\xE9soudre activ\xE9 et aucune action. L\u2019acquittement d\u2019une personne arr\xEAte le cycle pour tous. La lecture et l\u2019ouverture ne sont pas signal\xE9es de fa\xE7on fiable. Mobile uniquement ; sommeil et pr\xE9sence restent respect\xE9s. Aucun rejeu vocal ni rattrapage au red\xE9marrage. Une mise \xE0 jour conserve le compteur et relance l\u2019intervalle.","Deja ambos a 0 para desactivar. Si no, elige 60\u201386400 segundos y 1\u2013100 recordatorios, y a\xF1ade un bot\xF3n de confirmaci\xF3n con Resolver activado y sin acciones. La confirmaci\xF3n de una persona detiene el ciclo para todos. La lectura y la apertura no se notifican de forma fiable. Solo m\xF3vil; se respetan sue\xF1o y presencia. Sin repetir voz ni recuperar recordatorios tras reiniciar. Las actualizaciones conservan el contador y reinician el intervalo."],reminderCount:["Reminder attempts","Tentatives de rappel","Intentos de recordatorio"],nextReminder:["Next reminder","Prochain rappel","Pr\xF3ximo recordatorio"],reminder_attempted:["Reminder attempted","Rappel tent\xE9","Recordatorio intentado"],reminder_deferred:["Reminder deferred","Rappel diff\xE9r\xE9","Recordatorio aplazado"],iosSound:["iOS sound filename (optional)","Nom du fichier sonore iOS (facultatif)","Nombre del archivo de sonido iOS (opcional)"],iosSoundHelp:["Leave empty for the usual sound. The .wav, .caf or .aiff file must already be available in Companion on every selected iPhone and last less than 30 seconds. One playback per notification; leave reminders disabled for a single alert. Requires iOS mobile destinations and a priority other than Quiet.","Laisse vide pour le son habituel. Le fichier .wav, .caf ou .aiff doit d\xE9j\xE0 \xEAtre disponible dans Companion sur chaque iPhone s\xE9lectionn\xE9 et durer moins de 30 secondes. Une lecture par notification ; laisse les rappels d\xE9sactiv\xE9s pour une seule alerte. N\xE9cessite des destinations mobiles iOS et une priorit\xE9 autre que Discr\xE8te.","D\xE9jalo vac\xEDo para el sonido habitual. El archivo .wav, .caf o .aiff debe estar disponible en Companion en cada iPhone seleccionado y durar menos de 30 segundos. Una reproducci\xF3n por notificaci\xF3n; deja los recordatorios desactivados para una sola alerta. Requiere destinos m\xF3viles iOS y una prioridad distinta de Discreta."],quiet:["Quiet","Discr\xE8te","Discreta"],normal:["Normal","Normale","Normal"],important:["Important","Importante","Importante"],critical:["Critical","Critique","Cr\xEDtica"],priorityHelp:["Priority does not override sleep. Critical alerts also require device permission and platform support.","La priorit\xE9 ne contourne pas le sommeil. Les alertes critiques n\xE9cessitent aussi l\u2019autorisation de l\u2019appareil et une plateforme compatible.","La prioridad no ignora el sue\xF1o. Las alertas cr\xEDticas tambi\xE9n requieren permiso del dispositivo y soporte de la plataforma."],lifecycle:["Lifecycle","Cycle de vie","Ciclo de vida"],update:["Update current cycle","Actualiser le cycle actuel","Actualizar ciclo actual"],new:["Start a new cycle","D\xE9marrer un nouveau cycle","Iniciar un ciclo nuevo"],expiration:["Expiration in seconds (0 = unlimited)","Expiration en secondes (0 = illimit\xE9e)","Caducidad en segundos (0 = ilimitada)"],resolveOnClear:["Resolve globally when mobile clearing is reported","R\xE9soudre partout si le mobile signale un effacement","Resolver globalmente cuando el m\xF3vil informe de un borrado"],advanced:["Rich content","Contenu enrichi","Contenido enriquecido"],image:["Image URL","URL de l\u2019image","URL de imagen"],link:["Link to open","Lien \xE0 ouvrir","Enlace para abrir"],camera:["Camera","Cam\xE9ra","C\xE1mara"],icon:["Icon","Ic\xF4ne","Icono"],color:["Color","Couleur","Color"],timeout:["Android display timeout (seconds)","Dur\xE9e d\u2019affichage Android (secondes)","Duraci\xF3n de visualizaci\xF3n en Android (segundos)"],voiceMode:["Voice destinations","Destinations vocales","Destinos de voz"],explicit:["Selected speakers","Enceintes s\xE9lectionn\xE9es","Altavoces seleccionados"],occupied:["Occupied rooms","Pi\xE8ces occup\xE9es","Habitaciones ocupadas"],voiceMessage:["Voice text (optional)","Texte vocal (facultatif)","Texto de voz (opcional)"],volume:["Native volume % (optional)","Volume natif en % (facultatif)","Volumen nativo en % (opcional)"],buttons:["Buttons","Boutons","Botones"],addButton:["Add a button","Ajouter un bouton","A\xF1adir un bot\xF3n"],buttonLabel:["Button label","Libell\xE9 du bouton","Etiqueta del bot\xF3n"],buttonId:["Button ID","Identifiant du bouton","ID del bot\xF3n"],buttonKind:["Button behavior","Comportement du bouton","Comportamiento del bot\xF3n"],actionButton:["Run actions / resolve","Ex\xE9cuter des actions / r\xE9soudre","Ejecutar acciones / resolver"],uriButton:["Open a link","Ouvrir un lien","Abrir un enlace"],actions:["Home Assistant actions","Actions Home Assistant","Acciones de Home Assistant"],resolveAfter:["Resolve after successful actions","R\xE9soudre apr\xE8s r\xE9ussite des actions","Resolver tras acciones correctas"],actionEditorHelp:["The native action editor is available inside Home Assistant. Configure action sequences in the automation editor if it has not loaded yet.","L\u2019\xE9diteur natif d\u2019actions est disponible dans Home Assistant. Configure les s\xE9quences dans l\u2019\xE9diteur d\u2019automatisations s\u2019il n\u2019est pas encore charg\xE9.","El editor nativo est\xE1 disponible en Home Assistant. Configura las secuencias en el editor de automatizaciones si a\xFAn no se ha cargado."],noEntities:["No matching entities available","Aucune entit\xE9 correspondante disponible","No hay entidades coincidentes disponibles"],select:["Choose\u2026","Choisir\u2026","Elegir\u2026"],yes:["Yes","Oui","S\xED"],no:["No","Non","No"],reason:["Reason","Motif","Motivo"],asleep:["Asleep","Endormi","Dormido"],not_home:["Away from home","Absent du domicile","Fuera de casa"],away:["Away from home","Absent du domicile","Fuera de casa"],home:["At home","Au domicile","En casa"],presence_unknown:["Presence unknown","Pr\xE9sence inconnue","Presencia desconocida"],sleep_unknown:["Sleep unknown","Sommeil inconnu","Sue\xF1o desconocido"],location_unknown:["Location unavailable","Position indisponible","Ubicaci\xF3n no disponible"],missing_coordinates:["Location unavailable","Position indisponible","Ubicaci\xF3n no disponible"],eligible:["Eligible","\xC9ligible","Disponible"],not_nearest:["Another resident is closer","Un autre r\xE9sident est plus proche","Otro residente est\xE1 m\xE1s cerca"],unknown_presence:["Presence unknown","Pr\xE9sence inconnue","Presencia desconocida"],unknown_sleep:["Sleep unknown","Sommeil inconnu","Sue\xF1o desconocido"],at_home:["At home","Au domicile","En casa"],waiting:["Waiting","En attente","En espera"],notification_created:["Notification created","Notification cr\xE9\xE9e","Notificaci\xF3n creada"],notification_updated:["Notification updated","Notification actualis\xE9e","Notificaci\xF3n actualizada"],resolution:["Resolution recorded","R\xE9solution enregistr\xE9e","Resoluci\xF3n registrada"],button_received:["Button received","Bouton re\xE7u","Bot\xF3n recibido"],unavailable:["Unavailable","Indisponible","No disponible"],refreshing:["Refreshing\u2026","Actualisation\u2026","Actualizando\u2026"],reload:["Reload","Recharger","Recargar"],demo:["Local demonstration \xB7 simulated calls only","D\xE9monstration locale \xB7 appels simul\xE9s uniquement","Demostraci\xF3n local \xB7 solo llamadas simuladas"],previewOutcome:["Routing preview","Simulation du routage","Vista previa del enrutamiento"],sendOutcome:["Send result","R\xE9sultat de l\u2019envoi","Resultado del env\xEDo"],noResults:["No destinations","Aucune destination","Sin destinos"],waitingHelp:["Pending sends are cancelled as soon as this notification is resolved.","Les envois en attente sont annul\xE9s d\xE8s la r\xE9solution de cette notification.","Los env\xEDos pendientes se cancelan al resolver esta notificaci\xF3n."],actionsCount:["Configured actions","Actions configur\xE9es","Acciones configuradas"],removePerson:["Remove person","Supprimer la personne","Eliminar persona"],removeRoom:["Remove room","Supprimer la pi\xE8ce","Eliminar habitaci\xF3n"],deleted:["Deleted","Supprim\xE9","Eliminado"],cancel:["Cancel","Annuler","Cancelar"],confirm:["Confirm","Confirmer","Confirmar"],emptyMessage:["Enter a message before previewing or sending.","Saisis un message avant de simuler ou d\u2019envoyer.","Introduce un mensaje antes de previsualizar o enviar."]},Q=Object.fromEntries(Object.entries(pe).map(([n,i])=>[n,i[0]])),at=Object.fromEntries(Object.entries(pe).map(([n,i])=>[n,i[1]])),rt=Object.fromEntries(Object.entries(pe).map(([n,i])=>[n,i[2]]));function ue(n){let i=(n??"en").toLowerCase().split(/[-_]/)[0];return i==="fr"||i==="es"?i:"en"}function he(n,i){return{en:Q,fr:at,es:rt}[ue(i)][n]}function Ke(n,i){return n in Q?he(n,i):n}var We=X`
  :host {
    --bg: var(--primary-background-color, Canvas);
    --surface: var(--ha-card-background, var(--card-background-color, Canvas));
    --text: var(--primary-text-color, CanvasText);
    --secondary: var(--secondary-text-color, GrayText);
    --line: var(--divider-color, #dce0e5);
    --accent: var(--primary-color, #03a9f4);
    --selected: color-mix(in srgb, var(--accent) 10%, var(--surface));
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
    background: var(--bg);
    color: var(--text);
    font-family: var(--ha-font-family-body, Roboto, system-ui, sans-serif);
    font-size: var(--ha-font-size-m, 14px);
    line-height: 1.6;
    color-scheme: inherit;
  }
  * {
    box-sizing: border-box;
    scrollbar-width: thin;
  }
  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
  }
  [hidden] {
    display: none !important;
  }
  header {
    display: flex;
    align-items: center;
    gap: 24px;
    min-height: 60px;
    padding: 0 20px;
    background: var(--app-header-background-color, var(--surface));
    color: var(--app-header-text-color, var(--text));
    border-bottom: 1px solid var(--line);
    flex-shrink: 0;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  .brand svg {
    width: 25px;
    height: 25px;
    fill: currentColor;
  }
  h1 {
    font-size: 20px;
    margin: 0;
    letter-spacing: -0.02em;
  }
  h2 {
    font-size: 22px;
    line-height: 1.3;
    margin: 0 0 12px;
  }
  h3 {
    font-size: 16px;
    margin: 0 0 12px;
  }
  h2,
  h3,
  strong {
    overflow-wrap: anywhere;
  }
  p {
    margin: 8px 0 16px;
  }
  .help,
  small {
    color: var(--secondary);
  }
  .help {
    max-width: 75ch;
  }
  small {
    font-size: 12px;
    overflow-wrap: anywhere;
  }
  code {
    font-size: 12px;
    overflow-wrap: anywhere;
  }
  .grow {
    flex: 1;
    min-width: 0;
  }
  nav {
    display: flex;
    align-self: stretch;
    gap: 8px;
    min-width: 0;
  }
  nav button {
    position: relative;
    background: transparent;
    color: inherit;
    border: 0;
    border-radius: 0;
    padding: 12px 16px;
  }
  nav button[aria-current="page"]:after {
    content: "";
    position: absolute;
    inset-inline: 16px;
    bottom: 0;
    height: 3px;
    background: currentColor;
  }
  .sidebar-toggle {
    width: 48px;
    min-width: 48px;
    height: 48px;
    border: 0;
    background: transparent;
    color: inherit;
    padding: 12px;
  }
  .sidebar-toggle svg {
    width: 24px;
    fill: currentColor;
  }
  main {
    display: flex;
    flex: 1;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
  }
  .workspace {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    flex: 1;
    min-height: 0;
  }
  .rail {
    background: var(--surface);
    border-inline-end: 1px solid var(--line);
    padding: 16px 12px;
    overflow: auto;
    min-width: 0;
  }
  .detail {
    overflow: auto;
    min-width: 0;
    padding: 24px;
    scroll-padding: 16px;
  }
  .page {
    overflow: auto;
    flex: 1;
    min-width: 0;
    padding: 24px;
  }
  .page > section,
  .page > h2,
  .page > .help {
    max-width: 980px;
    margin-inline: auto;
  }
  .page > section {
    margin-bottom: 28px;
  }
  .row,
  .actions {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  .section-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }
  .section-heading h2,
  .section-heading h3 {
    margin: 0;
  }
  .section {
    padding: 20px 0;
    border-bottom: 1px solid var(--line);
  }
  .section:first-child {
    padding-top: 0;
  }
  .section:last-child {
    border-bottom: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr));
    gap: 4px 20px;
  }
  .device {
    margin: 12px 0;
    padding: 12px 0 12px 16px;
    border-inline-start: 2px solid var(--line);
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin: 8px 0;
    min-width: 0;
  }
  .check {
    flex-direction: row;
    align-items: center;
    gap: 10px;
    min-height: 30px;
    cursor: pointer;
  }
  .check input {
    width: 18px;
    height: 18px;
    min-height: 18px;
    flex-shrink: 0;
    accent-color: var(--accent);
  }
  input,
  textarea,
  select,
  button {
    font: inherit;
    color: inherit;
  }
  input,
  textarea,
  select {
    width: 100%;
    min-width: 0;
    min-height: 40px;
    padding: 8px 10px;
    background: var(--input-fill-color, var(--surface));
    border: 1px solid var(--input-outlined-idle-border-color, var(--line));
    border-radius: 8px;
    color: var(--input-ink-color, var(--text));
  }
  textarea {
    resize: vertical;
    min-height: 90px;
  }
  input:invalid {
    border-color: var(--error-color, #db4437);
  }
  button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    padding: 7px 12px;
    max-width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    cursor: pointer;
    line-height: 1.4;
  }
  button:hover:not(:disabled) {
    background: var(--selected);
  }
  button:disabled {
    opacity: 0.55;
    cursor: default;
  }
  button.primary {
    background: var(--accent);
    color: var(--text-primary-color, #fff);
    border-color: transparent;
  }
  button.danger {
    color: var(--error-color, #db4437);
  }
  .link {
    border: 0;
    background: transparent;
  }
  .field {
    min-width: 0;
    margin: 8px 0;
  }
  .field > span {
    display: block;
    margin-bottom: 6px;
  }
  ha-entity-picker,
  ha-selector {
    display: block;
    min-width: 0;
  }
  .choices {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr));
    gap: 0 12px;
  }
  .choices .check {
    margin: 4px 0;
    overflow-wrap: anywhere;
  }
  fieldset {
    border: 0;
    padding: 0;
    margin: 8px 0;
    min-width: 0;
  }
  legend {
    padding: 0;
    margin-bottom: 4px;
    font-weight: 500;
  }
  .filters {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin: 12px 0;
  }
  .filters button {
    padding: 6px 9px;
    border: 0;
    background: transparent;
    font-size: 12px;
  }
  .filters button[aria-pressed="true"] {
    background: var(--selected);
    color: var(--accent);
  }
  .notification-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .notification-list button {
    width: 100%;
    text-align: start;
    align-items: start;
    justify-content: start;
    flex-direction: column;
    border: 0;
    padding: 12px 10px;
    margin: 3px 0;
    background: transparent;
  }
  .notification-list button[aria-pressed="true"] {
    background: var(--selected);
  }
  .notification-list strong {
    font-weight: 500;
  }
  .badge {
    display: inline-block;
    font-size: 12px;
    color: var(--secondary);
  }
  .pending {
    color: var(--warning-color, #b87500);
  }
  .accepted,
  .resolved {
    color: var(--success-color, #2e7d32);
  }
  .failed {
    color: var(--error-color, #db4437);
  }
  .empty {
    max-width: 520px;
    margin: 8vh auto;
    padding: 24px;
  }
  .empty p {
    color: var(--secondary);
  }
  .back {
    display: none;
    margin-bottom: 16px;
  }
  .metadata {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
    gap: 16px;
    margin: 20px 0;
  }
  .metadata dt {
    font-size: 12px;
    color: var(--secondary);
  }
  .metadata dd {
    margin: 2px 0;
    overflow-wrap: anywhere;
  }
  .delivery {
    padding: 12px 0;
    border-bottom: 1px solid var(--line);
  }
  .delivery .row {
    justify-content: space-between;
  }
  .timeline {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .timeline li {
    border-inline-start: 2px solid var(--line);
    margin: 0 0 8px;
    padding: 6px 14px;
  }
  .body {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  .notice {
    padding: 12px 16px;
    margin: 10px 20px;
    background: var(--selected);
    border: 1px solid var(--line);
    border-radius: 8px;
    flex-shrink: 0;
    overflow-wrap: anywhere;
  }
  .notice.error {
    color: var(--error-color, #db4437);
  }
  .savebar {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px calc(12px + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid var(--line);
    background: var(--surface);
  }
  .savebar .grow {
    line-height: 1.4;
  }
  details {
    margin: 12px 0;
  }
  summary {
    cursor: pointer;
    min-height: 40px;
    padding: 8px 0;
    font-weight: 500;
  }
  details[open] > summary {
    margin-bottom: 8px;
  }
  .result {
    margin-top: 20px;
    border-top: 1px solid var(--line);
    padding-top: 16px;
  }
  .result ul {
    padding-inline-start: 20px;
  }
  .result li {
    overflow-wrap: anywhere;
  }
  .result dl {
    margin: 4px 0 8px 12px;
  }
  .result dt {
    font-size: 12px;
    color: var(--secondary);
  }
  .result dd {
    margin: 0 0 6px;
    overflow-wrap: anywhere;
  }
  .confirm {
    padding: 12px;
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }
  @media (max-width: 1100px) {
    .workspace {
      grid-template-columns: 240px minmax(0, 1fr);
    }
    .detail {
      padding: 20px;
    }
  }
  @media (max-width: 760px) {
    header {
      gap: 8px;
      padding: 4px 12px 0;
      flex-wrap: wrap;
      min-height: 60px;
    }
    .brand {
      gap: 8px;
    }
    h1 {
      font-size: 18px;
    }
    nav {
      width: 100%;
      gap: 2px;
      overflow: auto;
    }
    nav button {
      padding: 10px 8px;
      font-size: 12px;
      flex: 1;
      white-space: nowrap;
    }
    nav button[aria-current="page"]:after {
      inset-inline: 8px;
    }
    .workspace {
      display: block;
      overflow: hidden;
    }
    .rail {
      height: 100%;
      border: 0;
    }
    .workspace:not(.has-detail) .detail {
      display: none;
    }
    .workspace.has-detail .rail {
      display: none;
    }
    .workspace.has-detail .detail {
      height: 100%;
    }
    .detail,
    .page {
      padding: 18px 14px;
    }
    .back {
      display: inline-flex;
    }
    h2 {
      font-size: 20px;
    }
    .savebar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
    }
    .savebar .grow {
      grid-column: 1/-1;
      font-size: 12px;
    }
    .notice {
      margin: 8px 12px;
    }
    .empty {
      margin: 24px auto;
      padding: 14px;
    }
    .section-heading {
      flex-wrap: wrap;
    }
    .choices {
      grid-template-columns: 1fr;
    }
  }
  @media (pointer: coarse) {
    button,
    input,
    select,
    summary {
      min-height: 44px;
    }
    .check input {
      min-height: 20px;
      width: 20px;
      height: 20px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    * {
      scroll-behavior: auto !important;
      transition: none !important;
    }
  }
`;var me=class extends _{constructor(){super(...arguments);this.narrow=!1;this.draft=new O;this.page="notifications";this.selected="";this.filter="active";this.query="";this.error="";this.message="";this.saving=!1;this.busy=!1;this.request=ce();this.result=null;this.purging=!1;this.revisionTick=0;this.generation=0;this.admin=!1;this.resultKind="previewOutcome";this.beforeUnload=e=>{this.draft.dirty&&(e.preventDefault(),e.returnValue="")}}static{this.properties={hass:{attribute:!1},narrow:{type:Boolean},snapshot:{state:!0},page:{state:!0},selected:{state:!0},filter:{state:!0},query:{state:!0},error:{state:!0},message:{state:!0},saving:{state:!0},busy:{state:!0},request:{state:!0},result:{state:!0},purging:{state:!0},revisionTick:{state:!0}}}static{this.styles=We}connectedCallback(){super.connectedCallback(),window.addEventListener("beforeunload",this.beforeUnload),this.hass&&this.connect()}disconnectedCallback(){super.disconnectedCallback(),++this.generation,this.unsubscribe?.(),this.unsubscribe=void 0,this.connection=void 0,window.removeEventListener("beforeunload",this.beforeUnload)}updated(e){if(e.has("hass")){if(this.style.colorScheme=this.hass?.themes?.darkMode?"dark":"light",this.hass?.user?.is_admin===!1){this.revoke();return}this.hass?.connection!==this.connection&&this.connect()}}revoke(){++this.generation,this.unsubscribe?.(),this.unsubscribe=void 0,this.connection=void 0,this.snapshot=void 0,this.draft=new O,this.request=ce(),this.result=null,this.admin=!1,this.error="forbidden",this.message=""}get locale(){return this.hass?.locale?.language??this.hass?.language}t(e){return he(e,this.locale)}text(e){return Ke(e,this.locale)}get config(){return this.draft.value}get canAct(){return this.admin&&!this.busy&&!this.saving&&!this.draft.dirty&&!this.draft.conflict}async connect(){if(!this.hass||!this.isConnected)return;if(this.hass.user?.is_admin===!1){this.revoke();return}let e=++this.generation;this.unsubscribe?.(),this.connection=this.hass.connection,this.error="";try{let t=await this.connection.subscribeMessage(s=>{e===this.generation&&(this.admin=!0,this.receive(s))},{type:"hano/subscribe"});e!==this.generation?t():this.unsubscribe=t}catch(t){e===this.generation&&this.fail(t)}}receive(e){this.snapshot&&e.revision<this.snapshot.revision||(this.snapshot=e,this.saving||this.draft.receive(e.config,e.revision),this.requestUpdate())}fail(e){let t=ze(e);if(["unauthorized","forbidden"].includes(t)){this.revoke();return}this.error=t in Q?t:"error",["revision_conflict","conflict"].includes(t)&&(this.draft.conflict=!0)}touch(){this.revisionTick++,this.message="",this.requestUpdate()}valid(){let e=[...this.renderRoot.querySelectorAll("input,textarea,select")].find(t=>!t.validity.valid);return e?(e.reportValidity(),e.focus(),!1):!0}async save(){if(!this.admin||this.saving||this.draft.conflict||!this.valid())return;let e=R(this.config),t=this.generation;this.saving=!0,this.error="";try{let s=await this.hass.callWS({type:"hano/save",config:e,revision:this.draft.revision});if(t!==this.generation)return;this.draft.acknowledge(e,s.config,s.revision),this.receive(s),this.message="saved"}catch(s){t===this.generation&&this.fail(s)}finally{this.saving=!1,this.snapshot&&this.snapshot.revision>this.draft.revision&&this.draft.receive(this.snapshot.config,this.snapshot.revision),this.requestUpdate()}}discard(){this.snapshot&&this.draft.reset(this.snapshot.config,this.snapshot.revision),this.error="",this.message="",this.touch()}async action(e,t={}){if(!this.canAct)return;this.busy=!0,this.error="",this.message="";let s=this.generation;try{let o=await this.hass.callWS({type:e,...t});if(s!==this.generation)return;e==="hano/preview"||e==="hano/send"?(this.result=o,this.resultKind=e==="hano/preview"?"previewOutcome":"sendOutcome"):e==="hano/purge_history"?(this.purging=!1,this.message="purged"):this.message="resolved"}catch(o){s===this.generation&&this.fail(o)}finally{this.busy=!1}}test(e){if(!this.request.message.trim()){this.error="emptyMessage";return}this.valid()&&this.action(e?"hano/send":"hano/preview",{request:R(this.request)})}editRequest(e,t){this.request={...this.request,[e]:t},this.result=null}field(e,t,s,o="text",a={}){return r`<label
      >${this.t(e)}<input
        data-field=${e}
        .value=${String(t)}
        type=${o}
        ?required=${a.required}
        min=${a.min??d}
        max=${a.max??d}
        step=${a.step??d}
        @input=${c=>s(c.target.value)}
    /></label>`}check(e,t,s){return r`<label class="check"
      ><input
        data-field=${e}
        type="checkbox"
        .checked=${t}
        @change=${o=>s(o.target.checked)}
      />${this.t(e)}</label
    >`}select(e,t,s,o){return r`<label
      >${this.t(e)}<select
        data-field=${e}
        .value=${t}
        @change=${a=>o(a.target.value)}
      >
        ${s.map(a=>r`<option value=${a} .selected=${a===t}>${this.text(a)}</option>`)}
      </select></label
    >`}entity(e,t,s,o,a=!1){let c=this.snapshot?.catalog.entities.filter(u=>s.includes(u.domain))??[];return customElements.get("ha-entity-picker")?r`<div class="field">
        <ha-entity-picker
          .hass=${this.hass}
          .label=${this.t(e)}
          .value=${t||void 0}
          .includeDomains=${s}
          .allowCustomEntity=${!1}
          .required=${a}
          @value-changed=${u=>o(u.detail.value??"")}
        ></ha-entity-picker>
      </div>`:r`<label
      >${this.t(e)}<select
        data-field=${e}
        .value=${t}
        ?required=${a}
        @change=${u=>o(u.target.value)}
      >
        <option value="" .selected=${!t}>
          ${this.t(a?"select":"none")}
        </option>
        ${t&&!c.some(u=>u.entity_id===t)?r`<option value=${t} selected>${t} · ${this.t("unavailable")}</option>`:d}${c.map(u=>r`<option value=${u.entity_id} .selected=${t===u.entity_id}>${u.name} (${u.entity_id})</option>`)}
      </select></label
    >`}choices(e,t,s,o){let a=[...s,...t.filter(c=>!s.some(l=>l.id===c)).map(c=>({id:c,name:`${c} \xB7 ${this.t("unavailable")}`}))];return r`<fieldset>
      <legend>${this.t(e)}</legend>
      <div class="choices">
        ${a.length?a.map(c=>r`<label class="check"><input type="checkbox" .checked=${t.includes(c.id)} @change=${()=>o(Be(t,c.id))} />${c.name}</label>`):r`<small>${this.t("noEntities")}</small>`}
      </div>
    </fieldset>`}entities(e){return this.snapshot?.catalog.entities.filter(t=>e.includes(t.domain)).map(t=>({id:t.entity_id,name:t.name}))??[]}date(e){if(!e)return this.t("unlimited");let t=new Date(e);return Number.isNaN(t.valueOf())?e:new Intl.DateTimeFormat(this.locale??"en",{dateStyle:"medium",timeStyle:"short"}).format(t)}personName(e){return this.config.persons.find(t=>t.person_id===e)?.name||this.snapshot?.catalog.entities.find(t=>t.entity_id===e)?.name||e}notificationView(){let e=(this.snapshot?.notifications??[]).filter(s=>(this.filter==="history"?s.status!=="active":s.status==="active")&&(this.filter!=="pending"||s.deliveries.some(o=>o.status==="pending"))&&`${s.title} ${s.message} ${s.notification_id}`.toLocaleLowerCase().includes(this.query.toLocaleLowerCase())),t=this.snapshot?.notifications.find(s=>s.cycle_id===this.selected);return r`<div class="workspace ${t?"has-detail":""}">
      <aside class="rail">
        <h2>${this.t("notifications")}</h2>
        <label class="sr-only" for="search">${this.t("search")}</label
        ><input
          id="search"
          type="search"
          .value=${this.query}
          placeholder=${this.t("search")}
          @input=${s=>this.query=s.target.value}
        />
        <div class="filters">
          ${["active","pending","history"].map(s=>r`<button
                aria-pressed=${String(this.filter===s)}
                @click=${()=>{this.filter=s,this.selected=""}}
              >
                ${this.text(s)}
              </button>`)}
        </div>
        ${e.length?r`<ul class="notification-list">
                ${e.map(s=>r`<li>
                      <button
                        aria-pressed=${String(this.selected===s.cycle_id)}
                        @click=${()=>this.selected=s.cycle_id}
                      >
                        <strong
                          >${s.title||s.notification_id}</strong
                        ><small>${s.notification_id}</small
                        ><span
                          class="badge ${s.deliveries.some(o=>o.status==="pending")?"pending":s.status}"
                          >${this.text(s.deliveries.some(o=>o.status==="pending")&&s.status==="active"?"pending":s.status)}</span
                        >
                      </button>
                    </li>`)}
              </ul>`:r`<p class="help">${this.t("noNotifications")}</p>`}
      </aside>
      <article class="detail">
        ${t?this.notificationDetail(t):r`<div class="empty">
                <h2>${this.t("chooseNotification")}</h2>
                <p>${this.t("chooseHint")}</p>
              </div>`}
      </article>
    </div>`}notificationDetail(e){return r`<button class="back" @click=${()=>this.selected=""}>
        ← ${this.t("back")}
      </button>
      <div class="section-heading">
        <div>
          <h2>${e.title||e.notification_id}</h2>
          <small
            >${e.notification_id} ·
            ${this.text(e.status==="active"?"activeSingle":e.status)}</small
          >
        </div>
        ${e.status==="active"?r`<button class="primary" ?disabled=${!this.canAct} @click=${()=>void this.action("hano/resolve",{notification_id:e.notification_id})}>${this.t("resolve")}</button>`:d}
      </div>
      <p class="body">${e.message}</p>
      <dl class="metadata">
        ${[["created",e.created_at],["updated",e.updated_at],["expires",e.expires_at]].map(([t,s])=>r`<div>
              <dt>${this.t(t)}</dt>
              <dd>${this.date(s)}</dd>
            </div>`)}
        <div>
          <dt>${this.t("cycle")}</dt>
          <dd><code>${e.cycle_id}</code></dd>
        </div>
      </dl>
      <section class="section">
        <h3>${this.t("deliveries")}</h3>
        <p class="help">${this.t("evidence")}</p>
        ${e.deliveries.map(t=>r`<div class="delivery">
              <div class="row">
                <strong
                  >${t.person_id?this.personName(t.person_id):this.text(t.channel)}</strong
                ><span class="badge ${t.status}"
                  >${this.text(t.status)}</span
                >
              </div>
              <small>${t.target}</small
              >${t.reason?r`<div class="help">${this.text(t.reason)}</div>`:d}
              ${e.request.reminder_interval&&t.channel==="mobile"?r`<div class="help">${this.t("reminderCount")}: ${t.reminder_count??0} / ${e.request.reminder_limit}${t.next_reminder_at?r` · ${this.t("nextReminder")}: ${this.date(t.next_reminder_at)}`:d}</div>`:d}
            </div>`)}
      </section>
      <section class="section">
        <h3>${this.t("timeline")}</h3>
        <ul class="timeline">
          ${e.history.map(t=>r`<li>
                <small>${this.date(t.at)}</small>
                <div>${this.text(t.event)}</div>
                ${t.target?r`<div><small>${t.target}</small></div>`:d}${typeof t.detail=="string"&&t.detail?r`<div><small>${this.text(t.detail)}</small></div>`:d}
              </li>`)}
        </ul>
      </section>`}peopleView(){return r`<div class="page">
      <section>
        <div class="section-heading">
          <h2>${this.t("people")}</h2>
          <button
            @click=${()=>{this.config.persons.push({person_id:"",name:"",sleep_entity_id:"",devices:[]}),this.touch()}}
          >
            ${this.t("addPerson")}
          </button>
        </div>
        <p class="help">
          ${this.t(this.config.persons.length?"devicesHelp":"noPeople")}
        </p>
        ${U(this.config.persons,e=>e,e=>this.personEditor(e))}
      </section>
    </div>`}personEditor(e){let t=(s,o)=>{e[s]=o,this.touch()};return r`<section class="section">
      <div class="section-heading">
        <h3>
          ${e.name||this.personName(e.person_id)||this.t("person")}
        </h3>
        <button
          class="danger"
          aria-label=${this.t("removePerson")}
          @click=${()=>{this.config.persons=this.config.persons.filter(s=>s!==e),this.touch()}}
        >
          ${this.t("remove")}
        </button>
      </div>
      <div class="grid">
        ${this.entity("person",e.person_id,["person"],s=>t("person_id",s),!0)}${this.field("name",e.name,s=>t("name",s))}${this.entity("sleep",e.sleep_entity_id,["binary_sensor","input_boolean"],s=>t("sleep_entity_id",s))}
      </div>
      <h3>${this.t("devices")}</h3>
      ${U(e.devices,s=>s,s=>this.deviceEditor(e,s))}<button
        @click=${()=>{e.devices.push({type:"mobile",target:"",platform:"generic",device_id:""}),this.touch()}}
      >
        ${this.t("addDevice")}
      </button>
    </section>`}deviceEditor(e,t){let s=this.snapshot?.catalog.mobile_services??[];return r`<div class="device">
      <div class="grid">
        ${this.select("type",t.type,["mobile","notify"],o=>{t.type=o,t.target="",t.device_id="",t.platform="generic",this.touch()})}${t.type==="mobile"?r`<label
                >${this.t("target")}<select
                  .value=${t.target}
                  required
                  @change=${o=>{let a=o.target.value,c=s.find(l=>l.service===a);t.target=a,t.device_id=c?.device_id??"",t.platform=c?.platform??"generic",this.touch()}}
                >
                  <option value="">${this.t("select")}</option>
                  ${t.target&&!s.some(o=>o.service===t.target)?r`<option value=${t.target}>${t.target} · ${this.t("unavailable")}</option>`:d}${s.map(o=>r`<option value=${o.service} .selected=${t.target===o.service}>${o.name}</option>`)}
                </select></label
              >`:this.entity("target",t.target,["notify"],o=>{t.target=o,this.touch()},!0)}${t.type==="mobile"?r`${this.select("platform",t.platform,["ios","android","generic"],o=>{t.platform=o,this.touch()})}${this.field("deviceId",t.device_id,o=>{t.device_id=o,this.touch()})}`:d}
      </div>
      <button
        class="danger"
        @click=${()=>{e.devices=e.devices.filter(o=>o!==t),this.touch()}}
      >
        ${this.t("remove")}
      </button>
    </div>`}roomsView(){return r`<div class="page">
      <section>
        <div class="section-heading">
          <h2>${this.t("rooms")}</h2>
          <button
            @click=${()=>{this.config.rooms.push({id:de(),name:"",presence_entity_id:"",sleep_entity_id:"",media_player_entity_ids:[]}),this.touch()}}
          >
            ${this.t("addRoom")}
          </button>
        </div>
        <p class="help">${this.t("voiceHelp")}</p>
        ${this.config.rooms.length?d:r`<p class="help">${this.t("noRooms")}</p>`}${U(this.config.rooms,e=>e,e=>this.roomEditor(e))}
      </section>
    </div>`}roomEditor(e){return r`<section class="section">
      <div class="section-heading">
        <h3>${e.name||this.t("roomName")}</h3>
        <button
          class="danger"
          aria-label=${this.t("removeRoom")}
          @click=${()=>{this.config.rooms=this.config.rooms.filter(t=>t!==e),this.touch()}}
        >
          ${this.t("remove")}
        </button>
      </div>
      <div class="grid">
        ${this.field("roomName",e.name,t=>{e.name=t,this.touch()},"text",{required:!0})}<label
          >${this.t("area")}<select
            .value=${e.id}
            @change=${t=>{e.id=t.target.value;let s=this.snapshot?.catalog.areas.find(o=>o.area_id===e.id);s&&!e.name&&(e.name=s.name),this.touch()}}
          >
            ${this.snapshot?.catalog.areas.some(t=>t.area_id===e.id)?d:r`<option value=${e.id}>${e.name||this.t("none")}</option>`}${this.snapshot?.catalog.areas.map(t=>r`<option value=${t.area_id} .selected=${e.id===t.area_id}>${t.name}</option>`)}
          </select></label
        >${this.entity("occupancy",e.presence_entity_id,["binary_sensor","input_boolean"],t=>{e.presence_entity_id=t,this.touch()})}${this.entity("roomSleep",e.sleep_entity_id,["binary_sensor","input_boolean"],t=>{e.sleep_entity_id=t,this.touch()})}
      </div>
      ${this.choices("speakers",e.media_player_entity_ids,this.entities(["media_player"]),t=>{e.media_player_entity_ids=t,this.touch()})}
    </section>`}settingsView(){return r`<div class="page">
      <h2>${this.t("settings")}</h2>
      <section class="section">
        <h3>${this.t("defaults")}</h3>
        <div class="grid">
          ${this.entity("tts",this.config.tts_entity_id,["tts"],e=>{this.config.tts_entity_id=e,this.touch()})}${this.field("language",this.config.tts_language,e=>{this.config.tts_language=e,this.touch()})}
        </div>
        <details>
          <summary>${this.t("nativeVolume")}</summary>
          <p class="help">${this.t("nativeVolumeHelp")}</p>
          ${this.choices("speakers",this.config.native_volume_entity_ids,this.entities(["media_player"]),e=>{this.config.native_volume_entity_ids=e,this.touch()})}
        </details>
      </section>
      <section class="section">
        <h3>${this.t("privacy")}</h3>
        <p class="help">${this.t("privacyHelp")}</p>
        ${this.field("retention",this.config.history_days,e=>{this.config.history_days=Number(e),this.touch()},"number",{required:!0,min:1,max:3650,step:"1"})}${this.purging?r`<div class="confirm">
                <p>${this.t("confirmPurge")}</p>
                <div class="actions">
                  <button @click=${()=>this.purging=!1}>
                    ${this.t("cancel")}</button
                  ><button
                    class="danger"
                    ?disabled=${!this.canAct}
                    @click=${()=>void this.action("hano/purge_history")}
                  >
                    ${this.t("confirm")}
                  </button>
                </div>
              </div>`:r`<button
                class="danger"
                ?disabled=${!this.canAct}
                @click=${()=>this.purging=!0}
              >
                ${this.t("purge")}
              </button>`}
      </section>
      <section class="section">
        <h3>${this.t("tests")}</h3>
        <p class="help">${this.t("testHelp")}</p>
        ${this.composer()}${this.draft.dirty?r`<p class="help">${this.t("saveFirst")}</p>`:d}
        <div class="actions">
          <button ?disabled=${!this.canAct} @click=${()=>this.test(!1)}>
            ${this.t("preview")}</button
          ><button
            class="primary"
            ?disabled=${!this.canAct}
            @click=${()=>this.test(!0)}
          >
            ${this.t("send")}
          </button>
        </div>
        ${this.result?r`<div class="result" aria-live="polite">
                <h3>${this.t(this.resultKind)}</h3>
                ${this.resultView(this.result)}
              </div>`:d}
      </section>
    </div>`}composer(){let e=this.request;return r`<div class="grid">
        ${this.field("id",e.notification_id,t=>this.editRequest("notification_id",t))}${this.field("title",e.title,t=>this.editRequest("title",t))}
      </div>
      <label
        >${this.t("message")}<textarea
          data-field="message"
          .value=${e.message}
          @input=${t=>this.editRequest("message",t.target.value)}
        ></textarea>
      </label>
      <div class="grid">
        ${this.select("recipients",e.recipient_mode,["selected","all","present","absent","nearest"],t=>this.editRequest("recipient_mode",t))}${this.select("delivery",e.delivery,["immediate","when_available"],t=>this.editRequest("delivery",t))}
      </div>
      ${e.recipient_mode==="selected"?this.choices("people",e.person_entity_ids,this.config.persons.filter(t=>t.person_id).map(t=>({id:t.person_id,name:this.personName(t.person_id)})),t=>this.editRequest("person_entity_ids",t)):d}${e.recipient_mode==="nearest"?r`<p class="help">${this.t("nearestHelp")}</p>`:d}
      <details>
        <summary>${this.t("directDevices")}</summary>
        ${this.choices("directDevices",e.mobile_device_ids,this.snapshot?.catalog.mobile_devices.map(t=>({id:t.device_id,name:t.name}))??[],t=>this.editRequest("mobile_device_ids",t))}${this.choices("directNotify",e.notify_entity_ids,this.entities(["notify"]),t=>this.editRequest("notify_entity_ids",t))}
      </details>
      ${this.choices("channels",e.channels,["mobile","voice","persistent"].map(t=>({id:t,name:this.text(t)})),t=>this.editRequest("channels",t))}${this.check("respectSleep",e.respect_sleep,t=>this.editRequest("respect_sleep",t))}${this.select("priority",e.priority,["quiet","normal","important","critical"],t=>this.editRequest("priority",t))}
      <p class="help">${this.t("priorityHelp")}</p>
      ${this.field("iosSound",e.ios_sound??"",t=>this.editRequest("ios_sound",t))}
      <p class="help">${this.t("iosSoundHelp")}</p>
      <details>
        <summary>${this.t("lifecycle")}</summary>
        <div class="grid">
          ${this.select("cycle",e.cycle_mode,["update","new"],t=>this.editRequest("cycle_mode",t))}${this.field("expiration",e.expires_in,t=>this.editRequest("expires_in",Number(t)),"number",{min:0,step:"1"})}
        </div>
        ${this.check("resolveOnClear",e.resolve_on_clear,t=>this.editRequest("resolve_on_clear",t))}
        <div class="grid">
          ${this.field("reminderInterval",e.reminder_interval??0,t=>this.editRequest("reminder_interval",Number(t)),"number",{min:0,max:86400,step:"1"})}
          ${this.field("reminderLimit",e.reminder_limit??0,t=>this.editRequest("reminder_limit",Number(t)),"number",{min:0,max:100,step:"1"})}
        </div>
        <p class="help">${this.t("reminderHelp")}</p>
      </details>
      <details>
        <summary>${this.t("advanced")}</summary>
        <div class="grid">
          ${this.field("image",e.image_url,t=>this.editRequest("image_url",t))}${this.field("link",e.click_url,t=>this.editRequest("click_url",t))}${this.entity("camera",e.camera_entity_id,["camera"],t=>this.editRequest("camera_entity_id",t))}${this.field("icon",e.icon,t=>this.editRequest("icon",t))}${this.field("color",e.color,t=>this.editRequest("color",t))}${this.field("timeout",e.timeout,t=>this.editRequest("timeout",Number(t)),"number",{min:0,step:"1"})}
        </div>
      </details>
      ${e.channels.includes("voice")?r`<details open>
              <summary>${this.t("voice")}</summary>
              <p class="help">${this.t("voiceHelp")}</p>
              ${this.select("voiceMode",e.voice_mode,["explicit","occupied"],t=>this.editRequest("voice_mode",t))}${e.voice_mode==="explicit"?this.choices("speakers",e.media_player_entity_ids,this.entities(["media_player"]),t=>this.editRequest("media_player_entity_ids",t)):d}
              <div class="grid">
                ${this.entity("tts",e.tts_entity_id,["tts"],t=>this.editRequest("tts_entity_id",t))}${this.field("language",e.tts_language,t=>this.editRequest("tts_language",t))}${this.field("voiceMessage",e.voice_message,t=>this.editRequest("voice_message",t))}${this.field("volume",e.volume??"",t=>this.editRequest("volume",t===""?null:Number(t)),"number",{min:0,max:100,step:"1"})}
              </div>
            </details>`:d}
      <details>
        <summary>${this.t("buttons")} (${e.buttons.length})</summary>
        ${U(e.buttons,(t,s)=>s,(t,s)=>this.buttonEditor(t,s))}<button
          @click=${()=>this.editRequest("buttons",[...e.buttons,{id:`button_${de().slice(0,8)}`,label:"",uri:"",actions:[],resolve:!1}])}
        >
          ${this.t("addButton")}
        </button>
      </details>`}buttonEditor(e,t){let s=o=>this.editRequest("buttons",this.request.buttons.map((a,c)=>c===t?{...a,...o}:a));return r`<div class="device">
      <div class="grid">
        ${this.field("buttonLabel",e.label,o=>s({label:o}),"text",{required:!0})}${this.field("buttonId",e.id,o=>s({id:o}),"text",{required:!0})}
      </div>
      ${this.select("buttonKind",e.uri?"uriButton":"actionButton",["actionButton","uriButton"],o=>s(o==="uriButton"?{uri:"/",actions:[],resolve:!1}:{uri:""}))}${e.uri?this.field("link",e.uri,o=>s({uri:o}),"text",{required:!0}):r`<div class="field">
                <span>${this.t("actions")}</span>${customElements.get("ha-selector")?r`<ha-selector
                        .hass=${this.hass}
                        .selector=${{action:{}}}
                        .value=${e.actions}
                        @value-changed=${o=>s({actions:o.detail.value??[]})}
                      ></ha-selector>`:r`<p class="help">${this.t("actionEditorHelp")}</p>
                        <small
                          >${this.t("actionsCount")}:
                          ${e.actions.length}</small
                        >`}
              </div>
              ${this.check("resolveAfter",e.resolve,o=>s({resolve:o}))}`}<button
        class="danger"
        @click=${()=>this.editRequest("buttons",this.request.buttons.filter((o,a)=>a!==t))}
      >
        ${this.t("remove")}
      </button>
    </div>`}resultView(e,t=0){return t>5||e===void 0?d:e===null?r`—`:Array.isArray(e)?e.length?r`<ul>
            ${e.map(s=>r`<li>${this.resultView(s,t+1)}</li>`)}
          </ul>`:r`<small>${this.t("noResults")}</small>`:typeof e=="object"?r`<dl>
        ${Object.entries(e).filter(([s])=>!["actions","tokens","action_tokens","token","request"].includes(s)).map(([s,o])=>r`<dt>${this.text(s)}</dt>
                <dd>${this.resultView(o,t+1)}</dd>`)}
      </dl>`:r`${typeof e=="boolean"?this.t(e?"yes":"no"):this.text(String(e))}`}render(){let e=ue(this.locale);if(this.hass?.user?.is_admin===!1||this.error==="forbidden")return r`<div class="empty" lang=${e} role="alert">
        <h2>Hano</h2>
        <p>${this.t("forbidden")}</p>
      </div>`;let t=this.narrow||this.hass?.dockedSidebar==="always_hidden";return r`<header lang=${e}>
        ${t?r`<button
                class="sidebar-toggle"
                aria-label=${this.t("menu")}
                title=${this.t("menu")}
                @click=${()=>this.dispatchEvent(new CustomEvent("hass-toggle-menu",{detail:{open:!0},bubbles:!0,composed:!0}))}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"></path>
                </svg>
              </button>`:d}
        <div class="brand">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M12 22a2 2 0 002-2h-4a2 2 0 002 2m6-6V11a6 6 0 00-5-5.91V4a1 1 0 00-2 0v1.09A6 6 0 006 11v5l-2 2v1h16v-1z"
            ></path>
          </svg>
          <h1>Hano</h1>
        </div>
        <nav aria-label="Hano">
          ${["notifications","people","rooms","settings"].map(s=>r`<button
                aria-current=${this.page===s?"page":d}
                @click=${()=>{this.page=s,this.message=""}}
              >
                ${this.t(s)}
              </button>`)}
        </nav>
      </header>
      ${this.error?r`<div class="notice error" lang=${e} role="alert">${this.text(this.error)}${this.snapshot?d:r` <button @click=${()=>void this.connect()}>${this.t("retry")}</button>`}</div>`:d}${this.message?r`<div class="notice" lang=${e} role="status">${this.text(this.message)}</div>`:d}${this.draft.conflict?r`<div class="notice error" lang=${e} role="alert">${this.t("conflict")}</div>`:d}
      <main lang=${e}>
        ${this.snapshot?this.page==="notifications"?this.notificationView():this.page==="people"?this.peopleView():this.page==="rooms"?this.roomsView():this.settingsView():r`<div class="empty" role="status">${this.t("loading")}</div>`}
      </main>
      ${this.draft.dirty||this.draft.conflict?r`<footer class="savebar" lang=${e}>
              <div class="grow">${this.t("unsaved")}</div>
              <button ?disabled=${this.saving} @click=${()=>this.discard()}>
                ${this.t("discard")}</button
              ><button
                class="primary"
                ?disabled=${this.saving||this.draft.conflict}
                @click=${()=>void this.save()}
              >
                ${this.t(this.saving?"saving":"save")}
              </button>
            </footer>`:d}`}};customElements.define("hano-panel",me);export{me as HanoPanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
lit-html/directive.js:
lit-html/directives/repeat.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/directive-helpers.js:
  (**
   * @license
   * Copyright 2020 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
