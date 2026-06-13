(function(){const r=document.createElement("link").relList;if(r&&r.supports&&r.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))n(o);new MutationObserver(o=>{for(const s of o)if(s.type==="childList")for(const a of s.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&n(a)}).observe(document,{childList:!0,subtree:!0});function t(o){const s={};return o.integrity&&(s.integrity=o.integrity),o.referrerPolicy&&(s.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?s.credentials="include":o.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function n(o){if(o.ep)return;o.ep=!0;const s=t(o);fetch(o.href,s)}})();function fe(){const e=document.createElement("div");e.className="sidebar",e.style.cssText=`
    display: flex;
    flex-direction: column;
    width: 280px;
    height: 100vh;
    background-color: var(--panel);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    transition: width 0.3s ease;
    position: relative;
    z-index: 100;
    pointer-events: auto;
  `;const r=document.createElement("div");r.style.cssText=`
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  `;const t=document.createElement("div");t.textContent="⚡",t.style.cssText=`
    font-size: 24px;
    font-weight: bold;
  `;const n=document.createElement("span");n.textContent="DevForge",n.style.cssText=`
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `,r.appendChild(t),r.appendChild(n);const o=document.createElement("nav");o.style.cssText=`
    flex: 1;
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  `;const s=[{icon:"💬",label:"Chat",id:"nav-chat"},{icon:"📁",label:"Repository",id:"nav-repo"},{icon:"⚙️",label:"Configuration",id:"nav-config"},{icon:"🔧",label:"Tools",id:"nav-tools"},{icon:"📊",label:"Analytics",id:"nav-analytics"}];let a=null;s.forEach((g,p)=>{const m=document.createElement("button");m.id=g.id,m.style.cssText=`
      padding: 12px 16px;
      border: none;
      background: none;
      color: var(--text);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      transition: all 0.2s;
      font-family: inherit;
      text-align: left;
      border-left: 3px solid transparent;
      pointer-events: auto;
      width: 100%;
      z-index: 10;
    `,p===0&&(m.style.backgroundColor="var(--accent-dim)",m.style.borderLeftColor="var(--accent)",m.style.color="var(--accent)",a=m),m.addEventListener("mouseover",()=>{m!==a&&(m.style.backgroundColor="var(--border)")}),m.addEventListener("mouseout",()=>{m!==a&&(m.style.backgroundColor="transparent")}),m.addEventListener("click",()=>{a&&(a.style.backgroundColor="transparent",a.style.borderLeftColor="transparent",a.style.color="var(--text)"),m.style.backgroundColor="var(--accent-dim)",m.style.borderLeftColor="var(--accent)",m.style.color="var(--accent)",a=m}),m.addEventListener("keydown",c=>{const u=Array.from(o.querySelectorAll("button")),f=u.indexOf(m);c.key==="ArrowDown"&&f<u.length-1?(c.preventDefault(),u[f+1].focus()):c.key==="ArrowUp"&&f>0&&(c.preventDefault(),u[f-1].focus())});const v=document.createElement("span");v.textContent=g.icon,v.style.fontSize="18px";const h=document.createElement("span");h.textContent=g.label,m.appendChild(v),m.appendChild(h),o.appendChild(m)});const l=document.createElement("div");l.style.cssText=`
    padding: 16px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;const i=document.createElement("button");return i.id="sidebar-settings",i.style.cssText=`
    padding: 10px 12px;
    border: 1px solid var(--border);
    background: none;
    color: var(--text);
    cursor: pointer;
    border-radius: 6px;
    font-size: 13px;
    transition: all 0.2s;
    font-family: inherit;
    display: flex;
    align-items: center;
    gap: 8px;
  `,i.addEventListener("mouseover",()=>{i.style.backgroundColor="var(--border)"}),i.addEventListener("mouseout",()=>{i.style.backgroundColor="transparent"}),i.textContent="⚙️ Settings",l.appendChild(i),e.appendChild(r),e.appendChild(o),e.appendChild(l),e}const pe={create:fe};function me(e){const r=document.createElement("div");r.className="chat-window",r.style.cssText=`
    display: flex;
    flex-direction: column;
    flex: 1;
    background-color: var(--bg);
    border-radius: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
    min-height: 400px;
    position: relative;
    z-index: 1;
    pointer-events: auto;
  `;const t=document.createElement("div");t.className="messages-container",t.style.cssText=`
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  `,t.addEventListener("scroll",()=>{var l;(l=e==null?void 0:e.onScroll)==null||l.call(e,t.scrollTop)});const n=()=>{requestAnimationFrame(()=>{t.parentNode&&(t.scrollTop=t.scrollHeight)})},o=document.createElement("div");o.className="chat-empty-state",o.style.cssText=`
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
    gap: 12px;
  `;const s=document.createElement("div");s.textContent="💬",s.style.fontSize="48px";const a=document.createElement("p");return a.textContent="No messages yet. Start a conversation!",a.style.cssText=`
    margin: 0;
    font-size: 14px;
    max-width: 200px;
  `,o.appendChild(s),o.appendChild(a),t.appendChild(o),r.addMessage=l=>{o.parentNode===t&&o.remove(),t.appendChild(l),n()},r.clearMessages=()=>{t.innerHTML="";const l=document.createElement("div");l.className="chat-empty-state",l.style.cssText=o.style.cssText,l.appendChild(s.cloneNode(!0)),l.appendChild(a.cloneNode(!0)),t.appendChild(l)},r.getMessagesContainer=()=>t,r.appendChild(t),r}const ve={create:me};function ye(e){const r=document.createElement("div");r.className="app-layout",r.style.cssText=`
    display: flex;
    width: 100vw;
    height: 100vh;
    background-color: var(--bg);
    overflow: hidden;
  `;const t=document.createElement("div");t.className="sidebar-section",t.style.cssText=`
    width: 280px;
    height: 100vh;
    background-color: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
    overflow-y: auto;
  `,(e==null?void 0:e.showSidebar)===!1&&(t.style.width="0",t.style.borderRight="none");const n=document.createElement("div");n.className="main-section",n.style.cssText=`
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  `;const o=document.createElement("div");o.className="app-toolbar",o.style.cssText=`
    height: 50px;
    background-color: var(--panel);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 12px;
  `;const s=document.createElement("button");s.textContent="☰",s.style.cssText=`
    background: none;
    border: none;
    color: var(--text);
    font-size: 18px;
    cursor: pointer;
    padding: 4px 8px;
    transition: color 0.2s;
  `,s.addEventListener("mouseover",()=>{s.style.color="var(--accent)"}),s.addEventListener("mouseout",()=>{s.style.color="var(--text)"});let a=(e==null?void 0:e.showSidebar)!==!1;s.addEventListener("click",()=>{var d;a=!a,t.style.width=a?"280px":"0",t.style.borderRight=a?"1px solid var(--border)":"none",(d=e==null?void 0:e.onToggleSidebar)==null||d.call(e,a)});const l=document.createElement("div");l.className="app-breadcrumb",l.style.cssText=`
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
  `,l.textContent="📂 DevForge";const i=document.createElement("button");i.textContent="🌙",i.title="Toggle theme",i.style.cssText=`
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 16px;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 4px;
    transition: all 0.2s;
  `,i.addEventListener("mouseover",()=>{i.style.backgroundColor="var(--border)"}),i.addEventListener("mouseout",()=>{i.style.backgroundColor="transparent"});let g=!0;i.addEventListener("click",()=>{g=!g,document.documentElement.setAttribute("data-theme",g?"dark":"light"),i.textContent=g?"🌙":"☀️"}),o.appendChild(s),o.appendChild(l),o.appendChild(i);const p=document.createElement("div");p.className="content-wrapper",p.style.cssText=`
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 0;
    overflow: hidden;
  `;const m=document.createElement("div");m.className="main-content",m.style.cssText=`
    display: flex;
    flex-direction: column;
    overflow: auto;
    background-color: var(--bg);
  `;const x=document.createElement("div");x.style.cssText=`
    padding: 20px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    font-size: 14px;
  `,x.textContent="Main content area",m.appendChild(x);const v=document.createElement("div");v.className="context-panel",v.style.cssText=`
    width: 300px;
    background-color: var(--panel);
    border-left: 1px solid var(--border);
    overflow-y: auto;
    padding: 12px;
    transition: width 0.3s ease;
  `,(e==null?void 0:e.showContextPanel)===!1&&(v.style.width="0",v.style.borderLeft="none",v.style.padding="0");const h=document.createElement("h3");h.textContent="Context",h.style.cssText=`
    margin: 0 0 12px 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `,v.appendChild(h),p.appendChild(m),p.appendChild(v);const c=document.createElement("div");c.className="status-bar",c.style.cssText=`
    height: 30px;
    background-color: var(--panel);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 20px;
    font-size: 11px;
    color: var(--text-secondary);
  `;const u=document.createElement("div");u.textContent="✓ Ready",u.style.cssText="color: var(--green);";const f=document.createElement("div");return f.style.cssText="margin-left: auto;",f.textContent="Line 1, Col 1",c.appendChild(u),c.appendChild(f),n.appendChild(o),n.appendChild(p),n.appendChild(c),r.appendChild(t),r.appendChild(n),r.getSidebar=()=>t,r.getMainContent=()=>m,r.getContextPanel=()=>v,r.toggleSidebar=d=>{a=d,t.style.width=d?"280px":"0",t.style.borderRight=d?"1px solid var(--border)":"none"},r}const ge={create:ye},he={},Y=e=>{let r;const t=new Set,n=(p,m)=>{const x=typeof p=="function"?p(r):p;if(!Object.is(x,r)){const v=r;r=m??(typeof x!="object"||x===null)?x:Object.assign({},r,x),t.forEach(h=>h(r,v))}},o=()=>r,i={setState:n,getState:o,getInitialState:()=>g,subscribe:p=>(t.add(p),()=>t.delete(p)),destroy:()=>{(he?"production":void 0)!=="production"&&console.warn("[DEPRECATED] The `destroy` method will be unsupported in a future version. Instead use unsubscribe function returned by subscribe. Everything will be garbage-collected if store is garbage-collected."),t.clear()}},g=r=e(n,o,i);return i},xe=e=>e?Y(e):Y;function X(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var V={exports:{}},y={};/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var j=Symbol.for("react.transitional.element"),Ce=Symbol.for("react.portal"),Se=Symbol.for("react.fragment"),Ee=Symbol.for("react.strict_mode"),be=Symbol.for("react.profiler"),Te=Symbol.for("react.consumer"),we=Symbol.for("react.context"),_e=Symbol.for("react.forward_ref"),Ie=Symbol.for("react.suspense"),Re=Symbol.for("react.memo"),Z=Symbol.for("react.lazy"),Me=Symbol.for("react.activity"),B=Symbol.iterator;function ke(e){return e===null||typeof e!="object"?null:(e=B&&e[B]||e["@@iterator"],typeof e=="function"?e:null)}var ee={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},te=Object.assign,ne={};function _(e,r,t){this.props=e,this.context=r,this.refs=ne,this.updater=t||ee}_.prototype.isReactComponent={};_.prototype.setState=function(e,r){if(typeof e!="object"&&typeof e!="function"&&e!=null)throw Error("takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,e,r,"setState")};_.prototype.forceUpdate=function(e){this.updater.enqueueForceUpdate(this,e,"forceUpdate")};function re(){}re.prototype=_.prototype;function H(e,r,t){this.props=e,this.context=r,this.refs=ne,this.updater=t||ee}var U=H.prototype=new re;U.constructor=H;te(U,_.prototype);U.isPureReactComponent=!0;var J=Array.isArray;function F(){}var C={H:null,A:null,T:null,S:null},oe=Object.prototype.hasOwnProperty;function z(e,r,t){var n=t.ref;return{$$typeof:j,type:e,key:r,ref:n!==void 0?n:null,props:t}}function Ae(e,r){return z(e.type,r,e.props)}function $(e){return typeof e=="object"&&e!==null&&e.$$typeof===j}function Pe(e){var r={"=":"=0",":":"=2"};return"$"+e.replace(/[=:]/g,function(t){return r[t]})}var q=/\/+/g;function D(e,r){return typeof e=="object"&&e!==null&&e.key!=null?Pe(""+e.key):r.toString(36)}function De(e){switch(e.status){case"fulfilled":return e.value;case"rejected":throw e.reason;default:switch(typeof e.status=="string"?e.then(F,F):(e.status="pending",e.then(function(r){e.status==="pending"&&(e.status="fulfilled",e.value=r)},function(r){e.status==="pending"&&(e.status="rejected",e.reason=r)})),e.status){case"fulfilled":return e.value;case"rejected":throw e.reason}}throw e}function T(e,r,t,n,o){var s=typeof e;(s==="undefined"||s==="boolean")&&(e=null);var a=!1;if(e===null)a=!0;else switch(s){case"bigint":case"string":case"number":a=!0;break;case"object":switch(e.$$typeof){case j:case Ce:a=!0;break;case Z:return a=e._init,T(a(e._payload),r,t,n,o)}}if(a)return o=o(e),a=n===""?"."+D(e,0):n,J(o)?(t="",a!=null&&(t=a.replace(q,"$&/")+"/"),T(o,r,t,"",function(g){return g})):o!=null&&($(o)&&(o=Ae(o,t+(o.key==null||e&&e.key===o.key?"":(""+o.key).replace(q,"$&/")+"/")+a)),r.push(o)),1;a=0;var l=n===""?".":n+":";if(J(e))for(var i=0;i<e.length;i++)n=e[i],s=l+D(n,i),a+=T(n,r,t,s,o);else if(i=ke(e),typeof i=="function")for(e=i.call(e),i=0;!(n=e.next()).done;)n=n.value,s=l+D(n,i++),a+=T(n,r,t,s,o);else if(s==="object"){if(typeof e.then=="function")return T(De(e),r,t,n,o);throw r=String(e),Error("Objects are not valid as a React child (found: "+(r==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":r)+"). If you meant to render a collection of children, use an array instead.")}return a}function M(e,r,t){if(e==null)return e;var n=[],o=0;return T(e,n,"","",function(s){return r.call(t,s,o++)}),n}function Oe(e){if(e._status===-1){var r=e._result;r=r(),r.then(function(t){(e._status===0||e._status===-1)&&(e._status=1,e._result=t)},function(t){(e._status===0||e._status===-1)&&(e._status=2,e._result=t)}),e._status===-1&&(e._status=0,e._result=r)}if(e._status===1)return e._result.default;throw e._result}var G=typeof reportError=="function"?reportError:function(e){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var r=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof e=="object"&&e!==null&&typeof e.message=="string"?String(e.message):String(e),error:e});if(!window.dispatchEvent(r))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",e);return}console.error(e)},Le={map:M,forEach:function(e,r,t){M(e,function(){r.apply(this,arguments)},t)},count:function(e){var r=0;return M(e,function(){r++}),r},toArray:function(e){return M(e,function(r){return r})||[]},only:function(e){if(!$(e))throw Error("React.Children.only expected to receive a single React element child.");return e}};y.Activity=Me;y.Children=Le;y.Component=_;y.Fragment=Se;y.Profiler=be;y.PureComponent=H;y.StrictMode=Ee;y.Suspense=Ie;y.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=C;y.__COMPILER_RUNTIME={__proto__:null,c:function(e){return C.H.useMemoCache(e)}};y.cache=function(e){return function(){return e.apply(null,arguments)}};y.cacheSignal=function(){return null};y.cloneElement=function(e,r,t){if(e==null)throw Error("The argument must be a React element, but you passed "+e+".");var n=te({},e.props),o=e.key;if(r!=null)for(s in r.key!==void 0&&(o=""+r.key),r)!oe.call(r,s)||s==="key"||s==="__self"||s==="__source"||s==="ref"&&r.ref===void 0||(n[s]=r[s]);var s=arguments.length-2;if(s===1)n.children=t;else if(1<s){for(var a=Array(s),l=0;l<s;l++)a[l]=arguments[l+2];n.children=a}return z(e.type,o,n)};y.createContext=function(e){return e={$$typeof:we,_currentValue:e,_currentValue2:e,_threadCount:0,Provider:null,Consumer:null},e.Provider=e,e.Consumer={$$typeof:Te,_context:e},e};y.createElement=function(e,r,t){var n,o={},s=null;if(r!=null)for(n in r.key!==void 0&&(s=""+r.key),r)oe.call(r,n)&&n!=="key"&&n!=="__self"&&n!=="__source"&&(o[n]=r[n]);var a=arguments.length-2;if(a===1)o.children=t;else if(1<a){for(var l=Array(a),i=0;i<a;i++)l[i]=arguments[i+2];o.children=l}if(e&&e.defaultProps)for(n in a=e.defaultProps,a)o[n]===void 0&&(o[n]=a[n]);return z(e,s,o)};y.createRef=function(){return{current:null}};y.forwardRef=function(e){return{$$typeof:_e,render:e}};y.isValidElement=$;y.lazy=function(e){return{$$typeof:Z,_payload:{_status:-1,_result:e},_init:Oe}};y.memo=function(e,r){return{$$typeof:Re,type:e,compare:r===void 0?null:r}};y.startTransition=function(e){var r=C.T,t={};C.T=t;try{var n=e(),o=C.S;o!==null&&o(t,n),typeof n=="object"&&n!==null&&typeof n.then=="function"&&n.then(F,G)}catch(s){G(s)}finally{r!==null&&t.types!==null&&(r.types=t.types),C.T=r}};y.unstable_useCacheRefresh=function(){return C.H.useCacheRefresh()};y.use=function(e){return C.H.use(e)};y.useActionState=function(e,r,t){return C.H.useActionState(e,r,t)};y.useCallback=function(e,r){return C.H.useCallback(e,r)};y.useContext=function(e){return C.H.useContext(e)};y.useDebugValue=function(){};y.useDeferredValue=function(e,r){return C.H.useDeferredValue(e,r)};y.useEffect=function(e,r){return C.H.useEffect(e,r)};y.useEffectEvent=function(e){return C.H.useEffectEvent(e)};y.useId=function(){return C.H.useId()};y.useImperativeHandle=function(e,r,t){return C.H.useImperativeHandle(e,r,t)};y.useInsertionEffect=function(e,r){return C.H.useInsertionEffect(e,r)};y.useLayoutEffect=function(e,r){return C.H.useLayoutEffect(e,r)};y.useMemo=function(e,r){return C.H.useMemo(e,r)};y.useOptimistic=function(e,r){return C.H.useOptimistic(e,r)};y.useReducer=function(e,r,t){return C.H.useReducer(e,r,t)};y.useRef=function(e){return C.H.useRef(e)};y.useState=function(e){return C.H.useState(e)};y.useSyncExternalStore=function(e,r,t){return C.H.useSyncExternalStore(e,r,t)};y.useTransition=function(){return C.H.useTransition()};y.version="19.2.7";V.exports=y;var W=V.exports;const Fe=X(W);var se={exports:{}},ae={},ie={exports:{}},le={};/**
 * @license React
 * use-sync-external-store-shim.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var w=W;function Ne(e,r){return e===r&&(e!==0||1/e===1/r)||e!==e&&r!==r}var je=typeof Object.is=="function"?Object.is:Ne,He=w.useState,Ue=w.useEffect,ze=w.useLayoutEffect,$e=w.useDebugValue;function We(e,r){var t=r(),n=He({inst:{value:t,getSnapshot:r}}),o=n[0].inst,s=n[1];return ze(function(){o.value=t,o.getSnapshot=r,O(o)&&s({inst:o})},[e,t,r]),Ue(function(){return O(o)&&s({inst:o}),e(function(){O(o)&&s({inst:o})})},[e]),$e(t),t}function O(e){var r=e.getSnapshot;e=e.value;try{var t=r();return!je(e,t)}catch{return!0}}function Ye(e,r){return r()}var Be=typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"?Ye:We;le.useSyncExternalStore=w.useSyncExternalStore!==void 0?w.useSyncExternalStore:Be;ie.exports=le;var Je=ie.exports;/**
 * @license React
 * use-sync-external-store-shim/with-selector.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var P=W,qe=Je;function Ge(e,r){return e===r&&(e!==0||1/e===1/r)||e!==e&&r!==r}var Ke=typeof Object.is=="function"?Object.is:Ge,Qe=qe.useSyncExternalStore,Xe=P.useRef,Ve=P.useEffect,Ze=P.useMemo,et=P.useDebugValue;ae.useSyncExternalStoreWithSelector=function(e,r,t,n,o){var s=Xe(null);if(s.current===null){var a={hasValue:!1,value:null};s.current=a}else a=s.current;s=Ze(function(){function i(v){if(!g){if(g=!0,p=v,v=n(v),o!==void 0&&a.hasValue){var h=a.value;if(o(h,v))return m=h}return m=v}if(h=m,Ke(p,v))return h;var c=n(v);return o!==void 0&&o(h,c)?(p=v,h):(p=v,m=c)}var g=!1,p,m,x=t===void 0?null:t;return[function(){return i(r())},x===null?void 0:function(){return i(x())}]},[r,t,n,o]);var l=Qe(e,s[0],s[1]);return Ve(function(){a.hasValue=!0,a.value=l},[l]),et(l),l};se.exports=ae;var tt=se.exports;const nt=X(tt),ce={},{useDebugValue:rt}=Fe,{useSyncExternalStoreWithSelector:ot}=nt;let K=!1;const st=e=>e;function at(e,r=st,t){(ce?"production":void 0)!=="production"&&t&&!K&&(console.warn("[DEPRECATED] Use `createWithEqualityFn` instead of `create` or use `useStoreWithEqualityFn` instead of `useStore`. They can be imported from 'zustand/traditional'. https://github.com/pmndrs/zustand/discussions/1937"),K=!0);const n=ot(e.subscribe,e.getState,e.getServerState||e.getInitialState,r,t);return rt(n),n}const it=e=>{(ce?"production":void 0)!=="production"&&typeof e!="function"&&console.warn("[DEPRECATED] Passing a vanilla store will be unsupported in a future version. Instead use `import { useStore } from 'zustand'`.");const r=typeof e=="function"?xe(e):e,t=(n,o)=>at(r,n,o);return Object.assign(t,r),t},E=e=>it,A={BASE_URL:"/",DEV:!1,MODE:"production",PROD:!0,SSR:!1},N=new Map,k=e=>{const r=N.get(e);return r?Object.fromEntries(Object.entries(r.stores).map(([t,n])=>[t,n.getState()])):{}},lt=(e,r,t)=>{if(e===void 0)return{type:"untracked",connection:r.connect(t)};const n=N.get(t.name);if(n)return{type:"tracked",store:e,...n};const o={connection:r.connect(t),stores:{}};return N.set(t.name,o),{type:"tracked",store:e,...o}},ct=(e,r={})=>(t,n,o)=>{const{enabled:s,anonymousActionType:a,store:l,...i}=r;let g;try{g=(s??(A?"production":void 0)!=="production")&&window.__REDUX_DEVTOOLS_EXTENSION__}catch{}if(!g)return(A?"production":void 0)!=="production"&&s&&console.warn("[zustand devtools middleware] Please install/enable Redux devtools extension"),e(t,n,o);const{connection:p,...m}=lt(l,g,i);let x=!0;o.setState=(c,u,f)=>{const d=t(c,u);if(!x)return d;const S=f===void 0?{type:a||"anonymous"}:typeof f=="string"?{type:f}:f;return l===void 0?(p==null||p.send(S,n()),d):(p==null||p.send({...S,type:`${l}/${S.type}`},{...k(i.name),[l]:o.getState()}),d)};const v=(...c)=>{const u=x;x=!1,t(...c),x=u},h=e(o.setState,n,o);if(m.type==="untracked"?p==null||p.init(h):(m.stores[m.store]=o,p==null||p.init(Object.fromEntries(Object.entries(m.stores).map(([c,u])=>[c,c===m.store?h:u.getState()])))),o.dispatchFromDevtools&&typeof o.dispatch=="function"){let c=!1;const u=o.dispatch;o.dispatch=(...f)=>{(A?"production":void 0)!=="production"&&f[0].type==="__setState"&&!c&&(console.warn('[zustand devtools middleware] "__setState" action type is reserved to set state from the devtools. Avoid using it.'),c=!0),u(...f)}}return p.subscribe(c=>{var u;switch(c.type){case"ACTION":if(typeof c.payload!="string"){console.error("[zustand devtools middleware] Unsupported action format");return}return L(c.payload,f=>{if(f.type==="__setState"){if(l===void 0){v(f.state);return}Object.keys(f.state).length!==1&&console.error(`
                    [zustand devtools middleware] Unsupported __setState action format. 
                    When using 'store' option in devtools(), the 'state' should have only one key, which is a value of 'store' that was passed in devtools(),
                    and value of this only key should be a state object. Example: { "type": "__setState", "state": { "abc123Store": { "foo": "bar" } } }
                    `);const d=f.state[l];if(d==null)return;JSON.stringify(o.getState())!==JSON.stringify(d)&&v(d);return}o.dispatchFromDevtools&&typeof o.dispatch=="function"&&o.dispatch(f)});case"DISPATCH":switch(c.payload.type){case"RESET":return v(h),l===void 0?p==null?void 0:p.init(o.getState()):p==null?void 0:p.init(k(i.name));case"COMMIT":if(l===void 0){p==null||p.init(o.getState());return}return p==null?void 0:p.init(k(i.name));case"ROLLBACK":return L(c.state,f=>{if(l===void 0){v(f),p==null||p.init(o.getState());return}v(f[l]),p==null||p.init(k(i.name))});case"JUMP_TO_STATE":case"JUMP_TO_ACTION":return L(c.state,f=>{if(l===void 0){v(f);return}JSON.stringify(o.getState())!==JSON.stringify(f[l])&&v(f[l])});case"IMPORT_STATE":{const{nextLiftedState:f}=c.payload,d=(u=f.computedStates.slice(-1)[0])==null?void 0:u.state;if(!d)return;v(l===void 0?d:d[l]),p==null||p.send(null,f);return}case"PAUSE_RECORDING":return x=!x}return}}),h},b=ct,L=(e,r)=>{let t;try{t=JSON.parse(e)}catch(n){console.error("[zustand devtools middleware] Could not parse the received json",n)}t!==void 0&&r(t)};function dt(e,r){let t;try{t=e()}catch{return}return{getItem:o=>{var s;const a=i=>i===null?null:JSON.parse(i,void 0),l=(s=t.getItem(o))!=null?s:null;return l instanceof Promise?l.then(a):a(l)},setItem:(o,s)=>t.setItem(o,JSON.stringify(s,void 0)),removeItem:o=>t.removeItem(o)}}const R=e=>r=>{try{const t=e(r);return t instanceof Promise?t:{then(n){return R(n)(t)},catch(n){return this}}}catch(t){return{then(n){return this},catch(n){return R(n)(t)}}}},ut=(e,r)=>(t,n,o)=>{let s={getStorage:()=>localStorage,serialize:JSON.stringify,deserialize:JSON.parse,partialize:u=>u,version:0,merge:(u,f)=>({...f,...u}),...r},a=!1;const l=new Set,i=new Set;let g;try{g=s.getStorage()}catch{}if(!g)return e((...u)=>{console.warn(`[zustand persist middleware] Unable to update item '${s.name}', the given storage is currently unavailable.`),t(...u)},n,o);const p=R(s.serialize),m=()=>{const u=s.partialize({...n()});let f;const d=p({state:u,version:s.version}).then(S=>g.setItem(s.name,S)).catch(S=>{f=S});if(f)throw f;return d},x=o.setState;o.setState=(u,f)=>{x(u,f),m()};const v=e((...u)=>{t(...u),m()},n,o);let h;const c=()=>{var u;if(!g)return;a=!1,l.forEach(d=>d(n()));const f=((u=s.onRehydrateStorage)==null?void 0:u.call(s,n()))||void 0;return R(g.getItem.bind(g))(s.name).then(d=>{if(d)return s.deserialize(d)}).then(d=>{if(d)if(typeof d.version=="number"&&d.version!==s.version){if(s.migrate)return s.migrate(d.state,d.version);console.error("State loaded from storage couldn't be migrated since no migrate function was provided")}else return d.state}).then(d=>{var S;return h=s.merge(d,(S=n())!=null?S:v),t(h,!0),m()}).then(()=>{f==null||f(h,void 0),a=!0,i.forEach(d=>d(h))}).catch(d=>{f==null||f(void 0,d)})};return o.persist={setOptions:u=>{s={...s,...u},u.getStorage&&(g=u.getStorage())},clearStorage:()=>{g==null||g.removeItem(s.name)},getOptions:()=>s,rehydrate:()=>c(),hasHydrated:()=>a,onHydrate:u=>(l.add(u),()=>{l.delete(u)}),onFinishHydration:u=>(i.add(u),()=>{i.delete(u)})},c(),h||v},ft=(e,r)=>(t,n,o)=>{let s={storage:dt(()=>localStorage),partialize:c=>c,version:0,merge:(c,u)=>({...u,...c}),...r},a=!1;const l=new Set,i=new Set;let g=s.storage;if(!g)return e((...c)=>{console.warn(`[zustand persist middleware] Unable to update item '${s.name}', the given storage is currently unavailable.`),t(...c)},n,o);const p=()=>{const c=s.partialize({...n()});return g.setItem(s.name,{state:c,version:s.version})},m=o.setState;o.setState=(c,u)=>{m(c,u),p()};const x=e((...c)=>{t(...c),p()},n,o);o.getInitialState=()=>x;let v;const h=()=>{var c,u;if(!g)return;a=!1,l.forEach(d=>{var S;return d((S=n())!=null?S:x)});const f=((u=s.onRehydrateStorage)==null?void 0:u.call(s,(c=n())!=null?c:x))||void 0;return R(g.getItem.bind(g))(s.name).then(d=>{if(d)if(typeof d.version=="number"&&d.version!==s.version){if(s.migrate)return[!0,s.migrate(d.state,d.version)];console.error("State loaded from storage couldn't be migrated since no migrate function was provided")}else return[!1,d.state];return[!1,void 0]}).then(d=>{var S;const[de,ue]=d;if(v=s.merge(ue,(S=n())!=null?S:x),t(v,!0),de)return p()}).then(()=>{f==null||f(v,void 0),v=n(),a=!0,i.forEach(d=>d(v))}).catch(d=>{f==null||f(void 0,d)})};return o.persist={setOptions:c=>{s={...s,...c},c.storage&&(g=c.storage)},clearStorage:()=>{g==null||g.removeItem(s.name)},getOptions:()=>s,rehydrate:()=>h(),hasHydrated:()=>a,onHydrate:c=>(l.add(c),()=>{l.delete(c)}),onFinishHydration:c=>(i.add(c),()=>{i.delete(c)})},s.skipHydration||h(),v||x},pt=(e,r)=>"getStorage"in r||"serialize"in r||"deserialize"in r?((A?"production":void 0)!=="production"&&console.warn("[DEPRECATED] `getStorage`, `serialize` and `deserialize` options are deprecated. Use `storage` option instead."),ut(e,r)):ft(e,r),I=pt;let mt=0;E()(b(e=>({toasts:[],addToast:r=>{const t=`toast-${mt++}`,n=r.duration||3e3;return e(o=>({toasts:[...o.toasts,{...r,id:t}]})),n>0&&setTimeout(()=>{e(o=>({toasts:o.toasts.filter(s=>s.id!==t)}))},n),t},removeToast:r=>e(t=>({toasts:t.toasts.filter(n=>n.id!==r)})),clearToasts:()=>e({toasts:[]}),showSettingsModal:!1,showCommandPalette:!1,showDiffViewer:!1,showWritePanel:!1,showBatchPanel:!1,setSettingsModal:r=>e({showSettingsModal:r}),setCommandPalette:r=>e({showCommandPalette:r}),setDiffViewer:r=>e({showDiffViewer:r}),setWritePanel:r=>e({showWritePanel:r}),setBatchPanel:r=>e({showBatchPanel:r}),sidebarCollapsed:!1,showContextPanel:!0,setSidebarCollapsed:r=>e({sidebarCollapsed:r}),setContextPanel:r=>e({showContextPanel:r}),theme:"dark",setTheme:r=>{e({theme:r}),document.documentElement.setAttribute("data-theme",r),localStorage.setItem("devforge-theme",r)}}),{name:"UIStore"}));E()(b(I((e,r)=>({conversations:[],currentConversationId:null,isLoading:!1,currentInput:"",createConversation:t=>{const n=`conv-${Date.now()}`,o={id:n,title:t,messages:[],createdAt:new Date,updatedAt:new Date};return e(s=>({conversations:[...s.conversations,o],currentConversationId:n})),n},deleteConversation:t=>e(n=>({conversations:n.conversations.filter(o=>o.id!==t),currentConversationId:n.currentConversationId===t?null:n.currentConversationId})),setCurrentConversation:t=>e({currentConversationId:t,currentInput:""}),addMessage:(t,n)=>e(o=>({conversations:o.conversations.map(s=>s.id===t?{...s,messages:[...s.messages,n],updatedAt:new Date}:s)})),removeMessage:(t,n)=>e(o=>({conversations:o.conversations.map(s=>s.id===t?{...s,messages:s.messages.filter(a=>a.id!==n),updatedAt:new Date}:s)})),clearMessages:t=>e(n=>({conversations:n.conversations.map(o=>o.id===t?{...o,messages:[],updatedAt:new Date}:o)})),setCurrentInput:t=>e({currentInput:t}),setLoading:t=>e({isLoading:t}),getCurrentConversation:()=>{const t=r();return t.conversations.find(n=>n.id===t.currentConversationId)},getConversationMessages:t=>{const o=r().conversations.find(s=>s.id===t);return(o==null?void 0:o.messages)||[]},getTotalTokens:t=>{const o=r().conversations.find(s=>s.id===t);return(o==null?void 0:o.messages.reduce((s,a)=>s+(a.tokens||0),0))||0}}),{name:"chat-store",version:1}),{name:"ChatStore"}));E()(b(I((e,r)=>({repositories:[],currentRepoId:null,fileTree:[],selectedFileId:null,openFiles:[],searchQuery:"",filteredFiles:[],addRepository:t=>e(n=>({repositories:[...n.repositories,t],currentRepoId:n.currentRepoId||t.id})),removeRepository:t=>e(n=>({repositories:n.repositories.filter(o=>o.id!==t),currentRepoId:n.currentRepoId===t?null:n.currentRepoId})),setCurrentRepository:t=>e({currentRepoId:t}),setFileTree:t=>e({fileTree:t}),selectFile:t=>e({selectedFileId:t}),openFile:t=>e(n=>({openFiles:n.openFiles.includes(t)?n.openFiles:[...n.openFiles,t],selectedFileId:t})),closeFile:t=>e(n=>({openFiles:n.openFiles.filter(o=>o!==t),selectedFileId:n.selectedFileId===t?null:n.selectedFileId})),toggleFolder:t=>{const n=o=>o.map(s=>s.id===t?{...s,isOpen:!s.isOpen}:s.children?{...s,children:n(s.children)}:s);e(o=>({fileTree:n(o.fileTree)}))},setSearchQuery:t=>{e(n=>({searchQuery:t,filteredFiles:r().searchFiles(t)}))},searchFiles:t=>{if(!t)return[];const n=o=>o.flatMap(s=>{const a=s.name.toLowerCase().includes(t.toLowerCase()),l=s.children?n(s.children):[];return a?[{...s,children:l}]:l});return n(r().fileTree)},getCurrentRepository:()=>{const t=r();return t.repositories.find(n=>n.id===t.currentRepoId)},getFile:t=>{const n=o=>{for(const s of o){if(s.id===t)return s;if(s.children){const a=n(s.children);if(a)return a}}};return n(r().fileTree)},getOpenFileCount:()=>r().openFiles.length}),{name:"repo-store",version:1}),{name:"RepoStore"}));E()(b(I((e,r)=>({providers:[],activeProviderId:null,models:[],activeModelId:null,temperature:.7,maxTokens:2e3,topP:1,topK:0,featureFlags:{canaryDeployment:!1,betaFeatures:!1,autoSave:!0,diffViewer:!0,batchOperations:!0},addProvider:t=>e(n=>({providers:[...n.providers,t],activeProviderId:n.activeProviderId||t.id})),updateProvider:(t,n)=>e(o=>({providers:o.providers.map(s=>s.id===t?{...s,...n}:s)})),removeProvider:t=>e(n=>({providers:n.providers.filter(o=>o.id!==t),activeProviderId:n.activeProviderId===t?null:n.activeProviderId})),setActiveProvider:t=>e({activeProviderId:t}),addModel:t=>e(n=>({models:[...n.models,t],activeModelId:n.activeModelId||t.id})),updateModel:(t,n)=>e(o=>({models:o.models.map(s=>s.id===t?{...s,...n}:s)})),removeModel:t=>e(n=>({models:n.models.filter(o=>o.id!==t),activeModelId:n.activeModelId===t?null:n.activeModelId})),setActiveModel:t=>e({activeModelId:t}),updateSettings:t=>e(t),setFeatureFlag:(t,n)=>e(o=>({featureFlags:{...o.featureFlags,[t]:n}})),toggleFeatureFlag:t=>e(n=>({featureFlags:{...n.featureFlags,[t]:!n.featureFlags[t]}})),isFeatureEnabled:t=>r().featureFlags[t]||!1,getActiveProvider:()=>{const t=r();return t.providers.find(n=>n.id===t.activeProviderId)},getActiveModel:()=>{const t=r();return t.models.find(n=>n.id===t.activeModelId)},getProviderModels:t=>r().models.filter(o=>o.provider===t),isConfigurationValid:()=>{var s,a;const t=r(),n=(s=t.getActiveProvider)==null?void 0:s.call(t),o=(a=t.getActiveModel)==null?void 0:a.call(t);return!!(n!=null&&n.isConfigured&&o)}}),{name:"config-store",version:1}),{name:"ConfigStore"}));E()(b(I((e,r)=>({files:[],totalTokens:0,maxTokens:8e3,references:[],createdAt:new Date,lastUpdated:new Date,addFile:t=>e(n=>{const o=n.totalTokens+t.tokens;return o>n.maxTokens?(console.warn("Adding file would exceed token limit"),n):{files:[...n.files,t],totalTokens:o,lastUpdated:new Date}}),removeFile:t=>e(n=>{const o=n.files.find(s=>s.id===t);return{files:n.files.filter(s=>s.id!==t),totalTokens:n.totalTokens-((o==null?void 0:o.tokens)||0),lastUpdated:new Date}}),updateFile:(t,n)=>e(o=>{const s=o.files.find(i=>i.id===t);if(!s)return o;const a=(n.tokens||s.tokens)-s.tokens,l=o.totalTokens+a;return l>o.maxTokens?(console.warn("Updating file would exceed token limit"),o):{files:o.files.map(i=>i.id===t?{...i,...n}:i),totalTokens:l,lastUpdated:new Date}}),clearFiles:()=>e({files:[],totalTokens:0,lastUpdated:new Date}),addReference:t=>e(n=>({references:[...n.references,t],lastUpdated:new Date})),removeReference:t=>e(n=>({references:n.references.filter(o=>o.id!==t),lastUpdated:new Date})),clearReferences:()=>e({references:[],lastUpdated:new Date}),setMaxTokens:t=>e({maxTokens:t}),getAvailableTokens:()=>{const t=r();return t.maxTokens-t.totalTokens},canAddFile:t=>{const n=r();return n.totalTokens+t<=n.maxTokens},getContextSize:()=>r().files.length,getTokenUsage:()=>r().totalTokens,getTokenPercentage:()=>{const t=r();return t.totalTokens/t.maxTokens*100},hasRoom:t=>{const n=r();return n.totalTokens+t<=n.maxTokens}}),{name:"context-store",version:1}),{name:"ContextStore"}));E()(b(I((e,r)=>({memories:[],conversationMemories:[],recentContext:[],maxRecentContext:20,addMemory:t=>{const n=`mem-${Date.now()}`,o=new Date;return e(s=>({memories:[...s.memories,{...t,id:n,createdAt:o,updatedAt:o}]})),n},updateMemory:(t,n)=>e(o=>({memories:o.memories.map(s=>s.id===t?{...s,...n,updatedAt:new Date}:s)})),removeMemory:t=>e(n=>({memories:n.memories.filter(o=>o.id!==t)})),getMemory:t=>r().memories.find(o=>o.key===t),saveConversationMemory:t=>e(n=>n.conversationMemories.find(s=>s.conversationId===t.conversationId)?{conversationMemories:n.conversationMemories.map(s=>s.conversationId===t.conversationId?{...t,createdAt:s.createdAt,updatedAt:new Date}:s)}:{conversationMemories:[...n.conversationMemories,{...t,createdAt:new Date,updatedAt:new Date}]}),removeConversationMemory:t=>e(n=>({conversationMemories:n.conversationMemories.filter(o=>o.conversationId!==t)})),getConversationMemory:t=>r().conversationMemories.find(o=>o.conversationId===t),addToRecentContext:t=>e(n=>({recentContext:[t,...n.recentContext].slice(0,n.maxRecentContext)})),getRecentContext:()=>r().recentContext,clearRecentContext:()=>e({recentContext:[]}),getMemoriesByCategory:t=>r().memories.filter(o=>o.category===t),getAllMemories:()=>r().memories,getMemorySize:()=>{const t=r();return t.memories.length+t.conversationMemories.length}}),{name:"memory-store",version:1}),{name:"MemoryStore"}));E()(b(I((e,r)=>({dailyMetrics:[],modelStats:[],totalMessages:0,totalTokens:0,totalCost:0,periodStart:new Date(Date.now()-30*24*60*60*1e3),periodEnd:new Date,recordUsage:t=>e(n=>({dailyMetrics:[...n.dailyMetrics,{...t,timestamp:new Date}],totalMessages:n.totalMessages+t.messagesCount,totalTokens:n.totalTokens+t.tokensUsed,totalCost:n.totalCost+t.cost})),updateModelStats:(t,n,o,s)=>e(a=>a.modelStats.find(i=>i.model===t)?{modelStats:a.modelStats.map(i=>i.model===t?{...i,totalMessages:i.totalMessages+1,totalTokens:i.totalTokens+o,totalCost:i.totalCost+s,lastUsed:new Date}:i)}:{modelStats:[...a.modelStats,{model:t,provider:n,totalMessages:1,totalTokens:o,totalCost:s,lastUsed:new Date}]}),clearStats:()=>e({dailyMetrics:[],modelStats:[],totalMessages:0,totalTokens:0,totalCost:0}),setPeriod:(t,n)=>e({periodStart:t,periodEnd:n}),getDailyMetrics:()=>r().dailyMetrics,getMetricsForPeriod:(t,n)=>r().dailyMetrics.filter(s=>s.timestamp>=t&&s.timestamp<=n),getModelStats:()=>r().modelStats.sort((n,o)=>o.totalCost-n.totalCost),getTopModel:()=>r().modelStats.reduce((n,o)=>!n||o.totalCost>n.totalCost?o:n),getTotalCost:()=>r().totalCost,getAverageTokensPerMessage:()=>{const t=r();return t.totalMessages>0?Math.round(t.totalTokens/t.totalMessages):0}}),{name:"stats-store",version:1}),{name:"StatsStore"}));const Q=document.getElementById("app");if(Q){const e=ge.create({showSidebar:!0});Q.appendChild(e);const r=e.querySelector(".sidebar-section");if(r){const n=pe.create();r.appendChild(n)}const t=e.querySelector(".main-section");if(t){const n=ve.create();t.innerHTML="",t.appendChild(n)}}
//# sourceMappingURL=index-BFh6NE-8.js.map
