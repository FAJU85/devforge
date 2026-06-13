(function(){const n=document.createElement("link").relList;if(n&&n.supports&&n.supports("modulepreload"))return;for(const r of document.querySelectorAll('link[rel="modulepreload"]'))o(r);new MutationObserver(r=>{for(const s of r)if(s.type==="childList")for(const a of s.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&o(a)}).observe(document,{childList:!0,subtree:!0});function t(r){const s={};return r.integrity&&(s.integrity=r.integrity),r.referrerPolicy&&(s.referrerPolicy=r.referrerPolicy),r.crossOrigin==="use-credentials"?s.credentials="include":r.crossOrigin==="anonymous"?s.credentials="omit":s.credentials="same-origin",s}function o(r){if(r.ep)return;r.ep=!0;const s=t(r);fetch(r.href,s)}})();function Pe(e){const n=document.createElement("div");n.setAttribute("role","status"),n.setAttribute("aria-live","polite");const t={success:{bg:"var(--green)",icon:"✓"},error:{bg:"var(--red)",icon:"✕"},info:{bg:"var(--accent)",icon:"ℹ"},warning:{bg:"var(--yellow)",icon:"⚠"}},o=t[e.type]||t.info;n.style.cssText=`
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 6px;
    background-color: ${o.bg};
    color: white;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 300px;
    animation: slideIn 0.3s ease-out;
  `,n.id=e.id;const r=document.createElement("span");r.textContent=o.icon,r.style.cssText=`
    font-weight: bold;
    font-size: 16px;
    flex-shrink: 0;
  `;const s=document.createElement("span");s.textContent=e.text,s.style.cssText=`
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  `;const a=document.createElement("button");return a.textContent="×",a.setAttribute("aria-label","Close notification"),a.style.cssText=`
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    transition: opacity 0.2s;
    outline: none;
  `,a.addEventListener("mouseover",()=>{a.style.opacity="0.7"}),a.addEventListener("mouseout",()=>{a.style.opacity="1"}),a.addEventListener("focus",()=>{a.style.outline="2px solid white",a.style.outlineOffset="2px"}),a.addEventListener("blur",()=>{a.style.outline="none"}),a.addEventListener("click",()=>{n.style.animation="slideOut 0.3s ease-in",setTimeout(()=>e.onRemove(e.id),300)}),n.appendChild(r),n.appendChild(s),n.appendChild(a),e.duration&&e.duration>0&&setTimeout(()=>{n.style.animation="slideOut 0.3s ease-in",setTimeout(()=>e.onRemove(e.id),300)},e.duration),n}function Oe(){const e=document.createElement("div");e.id="toast-container",e.style.cssText=`
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
    max-height: 90vh;
    overflow-y: auto;
    z-index: 9999;
  `;const n=document.createElement("style");return n.textContent=`
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `,document.head.appendChild(n),e}const w={create:Pe,createContainer:Oe};function ze(e){const n=document.createElement("div");n.style.cssText=`
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9998;
    animation: fadeIn 0.2s ease-out;
    pointer-events: auto;
  `;const t=document.createElement("div");t.setAttribute("role","dialog"),t.setAttribute("aria-modal","true"),t.style.cssText=`
    background-color: var(--bg);
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 90%;
    animation: slideUp 0.3s ease-out;
    pointer-events: auto;
    position: relative;
    z-index: 1;
  `;const o=document.createElement("h2");o.textContent=e.title,o.style.cssText=`
    margin: 0 0 12px 0;
    color: var(--text);
    font-size: 18px;
    font-weight: 600;
  `;const r=document.createElement("p");r.textContent=e.message,r.style.cssText=`
    margin: 0 0 24px 0;
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.5;
  `;const s=document.createElement("div");s.style.cssText=`
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  `;const a=e.cancelText||"Cancel",i=e.confirmText||(e.type==="alert"?"OK":"Confirm"),c=p=>{n.style.animation="fadeOut 0.2s ease-in",t.style.animation="slideDown 0.2s ease-in",setTimeout(()=>{n.remove()},200)};if(e.type!=="alert"){const p=document.createElement("button");p.textContent=a,p.style.cssText=`
      padding: 8px 16px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background-color: var(--panel);
      color: var(--text);
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
    `,p.addEventListener("mouseover",()=>{p.style.backgroundColor="var(--border)"}),p.addEventListener("mouseout",()=>{p.style.backgroundColor="var(--panel)"}),p.addEventListener("click",()=>{e.onCancel&&e.onCancel(),c()}),s.appendChild(p)}const d=document.createElement("button");d.textContent=i,d.style.cssText=`
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `,d.addEventListener("mouseover",()=>{d.style.opacity="0.8"}),d.addEventListener("mouseout",()=>{d.style.opacity="1"}),d.addEventListener("click",()=>{e.onConfirm&&e.onConfirm(),c()}),s.appendChild(d);const u=p=>{p.target===n&&(e.onCancel&&e.onCancel(),c())},l=p=>{p.key==="Escape"&&(e.onCancel&&e.onCancel(),c(),document.removeEventListener("keydown",l))},h=()=>{setTimeout(()=>d.focus(),100)};n.addEventListener("click",u),document.addEventListener("keydown",l),t.appendChild(o),t.appendChild(r),t.appendChild(s),n.appendChild(t),h();const y=document.createElement("style");return y.textContent=`
    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    @keyframes slideDown {
      from {
        transform: translateY(0);
        opacity: 1;
      }
      to {
        transform: translateY(20px);
        opacity: 0;
      }
    }
  `,document.head.appendChild(y),n}const be={create:ze};function $e(){const e=document.createElement("div");e.className="sidebar",e.style.cssText=`
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
  `;const n=document.createElement("div");n.style.cssText=`
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  `;const t=document.createElement("div");t.textContent="⚡",t.style.cssText=`
    font-size: 24px;
    font-weight: bold;
  `;const o=document.createElement("span");o.textContent="DevForge",o.style.cssText=`
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `,n.appendChild(t),n.appendChild(o);const r=document.createElement("nav");r.style.cssText=`
    flex: 1;
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  `;const s=[{icon:"💬",label:"Chat",id:"nav-chat"},{icon:"📁",label:"Repository",id:"nav-repo"},{icon:"⚙️",label:"Configuration",id:"nav-config"},{icon:"🔧",label:"Tools",id:"nav-tools"},{icon:"📊",label:"Analytics",id:"nav-analytics"}];let a=null;s.forEach((d,u)=>{const l=document.createElement("button");l.id=d.id,l.style.cssText=`
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
    `,u===0&&(l.style.backgroundColor="var(--accent-dim)",l.style.borderLeftColor="var(--accent)",l.style.color="var(--accent)",a=l),l.addEventListener("mouseover",()=>{l!==a&&(l.style.backgroundColor="var(--border)")}),l.addEventListener("mouseout",()=>{l!==a&&(l.style.backgroundColor="transparent")}),l.addEventListener("click",()=>{a&&(a.style.backgroundColor="transparent",a.style.borderLeftColor="transparent",a.style.color="var(--text)"),l.style.backgroundColor="var(--accent-dim)",l.style.borderLeftColor="var(--accent)",l.style.color="var(--accent)",a=l}),l.addEventListener("keydown",m=>{const f=Array.from(r.querySelectorAll("button")),v=f.indexOf(l);m.key==="ArrowDown"&&v<f.length-1?(m.preventDefault(),f[v+1].focus()):m.key==="ArrowUp"&&v>0&&(m.preventDefault(),f[v-1].focus())});const y=document.createElement("span");y.textContent=d.icon,y.style.fontSize="18px";const p=document.createElement("span");p.textContent=d.label,l.appendChild(y),l.appendChild(p),r.appendChild(l)});const i=document.createElement("div");i.style.cssText=`
    padding: 16px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;const c=document.createElement("button");return c.id="sidebar-settings",c.style.cssText=`
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
  `,c.addEventListener("mouseover",()=>{c.style.backgroundColor="var(--border)"}),c.addEventListener("mouseout",()=>{c.style.backgroundColor="transparent"}),c.textContent="⚙️ Settings",i.appendChild(c),e.appendChild(n),e.appendChild(r),e.appendChild(i),e}const Fe={create:$e};function Ne(){const e=document.createElement("div");e.className="main-panel",e.style.cssText=`
    display: flex;
    flex-direction: column;
    flex: 1;
    height: 100vh;
    background-color: var(--bg);
    overflow: hidden;
    position: relative;
    z-index: 1;
    pointer-events: auto;
  `;const n=document.createElement("div");n.style.cssText=`
    display: flex;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    background-color: var(--panel);
    gap: 12px;
    overflow-x: auto;
  `;const t=document.createElement("div");t.style.cssText=`
    display: flex;
    gap: 4px;
    flex: 1;
  `,["Chat","Repository","Debug"].forEach((a,i)=>{const c=document.createElement("button");c.className="main-tab",c.textContent=a,c.style.cssText=`
      padding: 8px 16px;
      border: 1px solid var(--border);
      background-color: ${i===0?"var(--accent)":"transparent"};
      color: ${i===0?"var(--bg)":"var(--text)"};
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
      white-space: nowrap;
    `,c.addEventListener("mouseover",()=>{i!==0&&(c.style.backgroundColor="var(--border)")}),c.addEventListener("mouseout",()=>{i!==0&&(c.style.backgroundColor="transparent")}),c.addEventListener("click",()=>{document.querySelectorAll(".main-tab").forEach(d=>{d instanceof HTMLElement&&(d.style.backgroundColor="transparent",d.style.color="var(--text)")}),c.style.backgroundColor="var(--accent)",c.style.color="var(--bg)"}),t.appendChild(c)}),n.appendChild(t);const r=document.createElement("div");r.className="content-area",r.style.cssText=`
    flex: 1;
    overflow: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  `;const s=document.createElement("div");return s.style.cssText=`
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    font-size: 16px;
  `,s.textContent="Select a tab to get started",r.appendChild(s),e.appendChild(n),e.appendChild(r),e}const je={create:Ne};function He(){const e=document.createElement("div");e.className="settings-panel",e.style.cssText=`
    display: flex;
    gap: 20px;
    padding: 20px;
    background-color: var(--bg);
    height: 100%;
    overflow: auto;
  `;const n=document.createElement("nav");n.style.cssText=`
    width: 200px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-shrink: 0;
  `,[{title:"General",icon:"⚙️",id:"settings-general",items:[]},{title:"Appearance",icon:"🎨",id:"settings-appearance",items:[]},{title:"API Keys",icon:"🔑",id:"settings-keys",items:[]},{title:"Models",icon:"🤖",id:"settings-models",items:[]},{title:"Advanced",icon:"⚡",id:"settings-advanced",items:[]}].forEach((c,d)=>{const u=document.createElement("button");u.className="settings-nav-item",u.id=c.id,u.style.cssText=`
      padding: 12px 16px;
      border: 1px solid ${d===0?"var(--accent)":"transparent"};
      background-color: ${d===0?"var(--accent)":"transparent"};
      color: ${d===0?"var(--bg)":"var(--text)"};
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
      display: flex;
      align-items: center;
      gap: 10px;
      text-align: left;
    `,u.addEventListener("mouseover",()=>{d!==0&&(u.style.backgroundColor="var(--border)")}),u.addEventListener("mouseout",()=>{d!==0&&(u.style.backgroundColor="transparent")});const l=document.createElement("span");l.textContent=c.icon;const h=document.createElement("span");h.textContent=c.title,u.appendChild(l),u.appendChild(h),n.appendChild(u)});const o=document.createElement("div");o.style.cssText=`
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-width: 600px;
  `;const r=document.createElement("div");r.style.cssText=`
    display: flex;
    flex-direction: column;
    gap: 16px;
  `;const s=document.createElement("h2");s.textContent="General Settings",s.style.cssText=`
    margin: 0 0 12px 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
  `;const a=document.createElement("p");return a.textContent="Configure your DevForge workspace settings",a.style.cssText=`
    margin: 0;
    font-size: 13px;
    color: var(--text-secondary);
  `,r.appendChild(s),r.appendChild(a),[{label:"Auto-save changes",type:"toggle"},{label:"Show line numbers",type:"toggle"},{label:"Font size",type:"select"}].forEach(c=>{const d=document.createElement("div");d.style.cssText=`
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background-color: var(--panel);
      border-radius: 6px;
      border: 1px solid var(--border);
    `;const u=document.createElement("label");u.textContent=c.label,u.style.cssText=`
      color: var(--text);
      font-size: 14px;
      cursor: pointer;
    `;let l;c.type==="toggle"?(l=document.createElement("input"),l.type="checkbox",l.checked=!0,l.style.cssText=`
        cursor: pointer;
        width: 18px;
        height: 18px;
      `):(l=document.createElement("select"),l.innerHTML="<option>14px</option><option>16px</option><option>18px</option>",l.style.cssText=`
        padding: 6px 10px;
        border: 1px solid var(--border);
        background-color: var(--input-bg);
        color: var(--text);
        border-radius: 4px;
        cursor: pointer;
        font-size: 13px;
        font-family: inherit;
      `),d.appendChild(u),d.appendChild(l),r.appendChild(d)}),o.appendChild(r),e.appendChild(n),e.appendChild(o),e}const Be={create:He};function Ue(e){const n=document.createElement("div");n.className="command-palette-overlay",n.style.cssText=`
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    z-index: 9997;
    padding-top: 100px;
    animation: fadeIn 0.2s ease-out;
    pointer-events: none;
  `;const t=document.createElement("div");t.style.cssText=`
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: auto;
  `;const o=document.createElement("div");o.className="command-palette",o.style.cssText=`
    background-color: var(--panel);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    width: 90%;
    max-width: 600px;
    max-height: 70vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: slideDown 0.3s ease-out;
    pointer-events: auto;
    position: relative;
    z-index: 1;
  `;const r=document.createElement("div");r.style.cssText=`
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  `;const s=document.createElement("span");s.textContent="🔍",s.style.fontSize="18px";const a=document.createElement("input");a.type="text",a.placeholder="Search commands...",a.autofocus=!0,a.style.cssText=`
    flex: 1;
    border: none;
    background: none;
    color: var(--text);
    font-size: 16px;
    font-family: inherit;
    outline: none;
  `,r.appendChild(s),r.appendChild(a);const i=document.createElement("div");i.className="command-results",i.style.cssText=`
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  `;const c=l=>{i.innerHTML="";const h=l?e.commands.filter(p=>{var m;return p.label.toLowerCase().includes(l.toLowerCase())||((m=p.description)==null?void 0:m.toLowerCase().includes(l.toLowerCase()))||p.category.toLowerCase().includes(l.toLowerCase())}):e.commands;if(h.length===0){const p=document.createElement("div");p.style.cssText=`
        padding: 40px 20px;
        text-align: center;
        color: var(--text-secondary);
      `,p.textContent="No commands found",i.appendChild(p);return}const y={};h.forEach(p=>{y[p.category]||(y[p.category]=[]),y[p.category].push(p)}),Object.entries(y).forEach(([p,m])=>{const f=document.createElement("div");f.style.cssText=`
        padding: 8px 16px;
        padding-top: 12px;
        color: var(--text-secondary);
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      `,f.textContent=p,i.appendChild(f),m.forEach((v,g)=>{const b=document.createElement("button");if(b.className="command-item",b.style.cssText=`
          padding: 12px 16px;
          border: none;
          background: ${g===0?"var(--accent)":"transparent"};
          color: ${g===0?"var(--bg)":"var(--text)"};
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
          transition: all 0.1s;
          font-family: inherit;
          text-align: left;
          width: 100%;
        `,v.icon){const j=document.createElement("span");j.textContent=v.icon,j.style.fontSize="18px",b.appendChild(j)}const I=document.createElement("div");I.style.cssText=`
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        `;const L=document.createElement("div");L.textContent=v.label,L.style.fontWeight="500";const N=document.createElement("div");N.textContent=v.description||"",N.style.cssText=`
          font-size: 12px;
          opacity: 0.7;
        `,I.appendChild(L),v.description&&I.appendChild(N),b.appendChild(I),b.addEventListener("mouseover",()=>{b.style.backgroundColor="var(--accent)",b.style.color="var(--bg)"}),b.addEventListener("mouseout",()=>{b.style.backgroundColor="transparent",b.style.color="var(--text)"}),b.addEventListener("click",()=>{v.onSelect(),d()}),i.appendChild(b)})})};c(""),a.addEventListener("input",l=>{c(l.target.value)});const d=()=>{n.style.animation="fadeOut 0.2s ease-in",o.style.animation="slideUp 0.2s ease-in",setTimeout(()=>{var l;n.remove(),(l=e.onClose)==null||l.call(e)},200)};a.addEventListener("keydown",l=>{l.key==="Escape"&&d()}),t.addEventListener("click",()=>{d()});const u=document.createElement("style");return u.textContent=`
    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    @keyframes slideDown {
      from {
        transform: translateY(-20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(0);
        opacity: 1;
      }
      to {
        transform: translateY(-20px);
        opacity: 0;
      }
    }
  `,document.head.appendChild(u),o.appendChild(r),o.appendChild(i),n.appendChild(t),n.appendChild(o),setTimeout(()=>a.focus(),0),n}const Ye={create:Ue};function We(e){const n=document.createElement("div");n.className="notification-hub";const t=(e==null?void 0:e.position)||"top-right",o={"top-right":"top: 20px; right: 20px;","top-left":"top: 20px; left: 20px;","bottom-right":"bottom: 20px; right: 20px;","bottom-left":"bottom: 20px; left: 20px;"};n.style.cssText=`
    position: fixed;
    ${o[t]}
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
    z-index: 9999;
  `;const r=a=>{const i=document.createElement("div");i.className=`notification notification-${a.type}`,i.id=a.id;const d={success:{bg:"rgba(16, 185, 129, 0.1)",text:"var(--green)",icon:"✓"},error:{bg:"rgba(239, 68, 68, 0.1)",text:"var(--red)",icon:"✕"},info:{bg:"rgba(59, 130, 246, 0.1)",text:"var(--accent)",icon:"ℹ"},warning:{bg:"rgba(245, 158, 11, 0.1)",text:"var(--yellow)",icon:"⚠"}}[a.type];i.style.cssText=`
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px;
      background-color: ${d.bg};
      border-left: 3px solid ${d.text};
      border-radius: 6px;
      color: var(--text);
      font-size: 13px;
      animation: slideIn 0.3s ease-out;
    `;const u=document.createElement("div");u.style.cssText=`
      display: flex;
      align-items: center;
      gap: 8px;
    `;const l=document.createElement("span");l.textContent=d.icon,l.style.cssText=`
      color: ${d.text};
      font-weight: bold;
      font-size: 16px;
    `;const h=document.createElement("span");h.textContent=a.title,h.style.cssText=`
      font-weight: 600;
      color: var(--text);
    `;const y=document.createElement("button");if(y.textContent="✕",y.style.cssText=`
      background: none;
      border: none;
      color: ${d.text};
      cursor: pointer;
      font-size: 16px;
      padding: 0;
      margin-left: auto;
      transition: opacity 0.2s;
    `,y.addEventListener("click",()=>{i.style.animation="slideOut 0.2s ease-in",setTimeout(()=>{i.remove()},200)}),u.appendChild(l),u.appendChild(h),u.appendChild(y),i.appendChild(u),a.message){const p=document.createElement("div");p.textContent=a.message,p.style.cssText=`
        color: var(--text-secondary);
        font-size: 12px;
        line-height: 1.4;
      `,i.appendChild(p)}if(a.actions&&a.actions.length>0){const p=document.createElement("div");p.style.cssText=`
        display: flex;
        gap: 8px;
        margin-top: 8px;
      `,a.actions.forEach(m=>{const f=document.createElement("button");f.textContent=m.label,f.style.cssText=`
          padding: 4px 10px;
          border: 1px solid ${d.text};
          border-radius: 3px;
          background-color: transparent;
          color: ${d.text};
          cursor: pointer;
          font-size: 11px;
          font-weight: 500;
          transition: all 0.2s;
          font-family: inherit;
        `,f.addEventListener("mouseover",()=>{f.backgroundColor=d.text,f.style.color="white"}),f.addEventListener("mouseout",()=>{f.style.backgroundColor="transparent",f.style.color=d.text}),f.addEventListener("click",()=>{m.onClick(),y.click()}),p.appendChild(f)}),i.appendChild(p)}if(n.appendChild(i),a.duration!==0){const p=a.duration||3e3;setTimeout(()=>{y.click()},p)}},s=document.createElement("style");return document.head.querySelector("style[data-notification-animations]")||(s.setAttribute("data-notification-animations","true"),s.textContent=`
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateX(${t.includes("right")?"400px":"-400px"});
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      @keyframes slideOut {
        to {
          opacity: 0;
          transform: translateX(${t.includes("right")?"400px":"-400px"});
        }
      }
    `,document.head.appendChild(s)),n.notify=r,n.success=(a,i)=>{r({id:`notification-${Date.now()}`,title:a,message:i,type:"success"})},n.error=(a,i)=>{r({id:`notification-${Date.now()}`,title:a,message:i,type:"error"})},n.info=(a,i)=>{r({id:`notification-${Date.now()}`,title:a,message:i,type:"info"})},n.warning=(a,i)=>{r({id:`notification-${Date.now()}`,title:a,message:i,type:"warning"})},n}const Je={create:We},Ke={},Z=e=>{let n;const t=new Set,o=(u,l)=>{const h=typeof u=="function"?u(n):u;if(!Object.is(h,n)){const y=n;n=l??(typeof h!="object"||h===null)?h:Object.assign({},n,h),t.forEach(p=>p(n,y))}},r=()=>n,c={setState:o,getState:r,getInitialState:()=>d,subscribe:u=>(t.add(u),()=>t.delete(u)),destroy:()=>{(Ke?"production":void 0)!=="production"&&console.warn("[DEPRECATED] The `destroy` method will be unsupported in a future version. Instead use unsubscribe function returned by subscribe. Everything will be garbage-collected if store is garbage-collected."),t.clear()}},d=n=e(o,r,c);return c},Xe=e=>e?Z(e):Z;function Ce(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var Ee={exports:{}},x={};/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var K=Symbol.for("react.transitional.element"),Ge=Symbol.for("react.portal"),qe=Symbol.for("react.fragment"),Qe=Symbol.for("react.strict_mode"),Ve=Symbol.for("react.profiler"),Ze=Symbol.for("react.consumer"),et=Symbol.for("react.context"),tt=Symbol.for("react.forward_ref"),nt=Symbol.for("react.suspense"),ot=Symbol.for("react.memo"),we=Symbol.for("react.lazy"),rt=Symbol.for("react.activity"),ee=Symbol.iterator;function st(e){return e===null||typeof e!="object"?null:(e=ee&&e[ee]||e["@@iterator"],typeof e=="function"?e:null)}var Te={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},Se=Object.assign,ke={};function A(e,n,t){this.props=e,this.context=n,this.refs=ke,this.updater=t||Te}A.prototype.isReactComponent={};A.prototype.setState=function(e,n){if(typeof e!="object"&&typeof e!="function"&&e!=null)throw Error("takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,e,n,"setState")};A.prototype.forceUpdate=function(e){this.updater.enqueueForceUpdate(this,e,"forceUpdate")};function Ie(){}Ie.prototype=A.prototype;function X(e,n,t){this.props=e,this.context=n,this.refs=ke,this.updater=t||Te}var G=X.prototype=new Ie;G.constructor=X;Se(G,A.prototype);G.isPureReactComponent=!0;var te=Array.isArray;function W(){}var C={H:null,A:null,T:null,S:null},_e=Object.prototype.hasOwnProperty;function q(e,n,t){var o=t.ref;return{$$typeof:K,type:e,key:n,ref:o!==void 0?o:null,props:t}}function at(e,n){return q(e.type,n,e.props)}function Q(e){return typeof e=="object"&&e!==null&&e.$$typeof===K}function it(e){var n={"=":"=0",":":"=2"};return"$"+e.replace(/[=:]/g,function(t){return n[t]})}var ne=/\/+/g;function H(e,n){return typeof e=="object"&&e!==null&&e.key!=null?it(""+e.key):n.toString(36)}function ct(e){switch(e.status){case"fulfilled":return e.value;case"rejected":throw e.reason;default:switch(typeof e.status=="string"?e.then(W,W):(e.status="pending",e.then(function(n){e.status==="pending"&&(e.status="fulfilled",e.value=n)},function(n){e.status==="pending"&&(e.status="rejected",e.reason=n)})),e.status){case"fulfilled":return e.value;case"rejected":throw e.reason}}throw e}function _(e,n,t,o,r){var s=typeof e;(s==="undefined"||s==="boolean")&&(e=null);var a=!1;if(e===null)a=!0;else switch(s){case"bigint":case"string":case"number":a=!0;break;case"object":switch(e.$$typeof){case K:case Ge:a=!0;break;case we:return a=e._init,_(a(e._payload),n,t,o,r)}}if(a)return r=r(e),a=o===""?"."+H(e,0):o,te(r)?(t="",a!=null&&(t=a.replace(ne,"$&/")+"/"),_(r,n,t,"",function(d){return d})):r!=null&&(Q(r)&&(r=at(r,t+(r.key==null||e&&e.key===r.key?"":(""+r.key).replace(ne,"$&/")+"/")+a)),n.push(r)),1;a=0;var i=o===""?".":o+":";if(te(e))for(var c=0;c<e.length;c++)o=e[c],s=i+H(o,c),a+=_(o,n,t,s,r);else if(c=st(e),typeof c=="function")for(e=c.call(e),c=0;!(o=e.next()).done;)o=o.value,s=i+H(o,c++),a+=_(o,n,t,s,r);else if(s==="object"){if(typeof e.then=="function")return _(ct(e),n,t,o,r);throw n=String(e),Error("Objects are not valid as a React child (found: "+(n==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":n)+"). If you meant to render a collection of children, use an array instead.")}return a}function O(e,n,t){if(e==null)return e;var o=[],r=0;return _(e,o,"","",function(s){return n.call(t,s,r++)}),o}function lt(e){if(e._status===-1){var n=e._result;n=n(),n.then(function(t){(e._status===0||e._status===-1)&&(e._status=1,e._result=t)},function(t){(e._status===0||e._status===-1)&&(e._status=2,e._result=t)}),e._status===-1&&(e._status=0,e._result=n)}if(e._status===1)return e._result.default;throw e._result}var oe=typeof reportError=="function"?reportError:function(e){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var n=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof e=="object"&&e!==null&&typeof e.message=="string"?String(e.message):String(e),error:e});if(!window.dispatchEvent(n))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",e);return}console.error(e)},dt={map:O,forEach:function(e,n,t){O(e,function(){n.apply(this,arguments)},t)},count:function(e){var n=0;return O(e,function(){n++}),n},toArray:function(e){return O(e,function(n){return n})||[]},only:function(e){if(!Q(e))throw Error("React.Children.only expected to receive a single React element child.");return e}};x.Activity=rt;x.Children=dt;x.Component=A;x.Fragment=qe;x.Profiler=Ve;x.PureComponent=X;x.StrictMode=Qe;x.Suspense=nt;x.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=C;x.__COMPILER_RUNTIME={__proto__:null,c:function(e){return C.H.useMemoCache(e)}};x.cache=function(e){return function(){return e.apply(null,arguments)}};x.cacheSignal=function(){return null};x.cloneElement=function(e,n,t){if(e==null)throw Error("The argument must be a React element, but you passed "+e+".");var o=Se({},e.props),r=e.key;if(n!=null)for(s in n.key!==void 0&&(r=""+n.key),n)!_e.call(n,s)||s==="key"||s==="__self"||s==="__source"||s==="ref"&&n.ref===void 0||(o[s]=n[s]);var s=arguments.length-2;if(s===1)o.children=t;else if(1<s){for(var a=Array(s),i=0;i<s;i++)a[i]=arguments[i+2];o.children=a}return q(e.type,r,o)};x.createContext=function(e){return e={$$typeof:et,_currentValue:e,_currentValue2:e,_threadCount:0,Provider:null,Consumer:null},e.Provider=e,e.Consumer={$$typeof:Ze,_context:e},e};x.createElement=function(e,n,t){var o,r={},s=null;if(n!=null)for(o in n.key!==void 0&&(s=""+n.key),n)_e.call(n,o)&&o!=="key"&&o!=="__self"&&o!=="__source"&&(r[o]=n[o]);var a=arguments.length-2;if(a===1)r.children=t;else if(1<a){for(var i=Array(a),c=0;c<a;c++)i[c]=arguments[c+2];r.children=i}if(e&&e.defaultProps)for(o in a=e.defaultProps,a)r[o]===void 0&&(r[o]=a[o]);return q(e,s,r)};x.createRef=function(){return{current:null}};x.forwardRef=function(e){return{$$typeof:tt,render:e}};x.isValidElement=Q;x.lazy=function(e){return{$$typeof:we,_payload:{_status:-1,_result:e},_init:lt}};x.memo=function(e,n){return{$$typeof:ot,type:e,compare:n===void 0?null:n}};x.startTransition=function(e){var n=C.T,t={};C.T=t;try{var o=e(),r=C.S;r!==null&&r(t,o),typeof o=="object"&&o!==null&&typeof o.then=="function"&&o.then(W,oe)}catch(s){oe(s)}finally{n!==null&&t.types!==null&&(n.types=t.types),C.T=n}};x.unstable_useCacheRefresh=function(){return C.H.useCacheRefresh()};x.use=function(e){return C.H.use(e)};x.useActionState=function(e,n,t){return C.H.useActionState(e,n,t)};x.useCallback=function(e,n){return C.H.useCallback(e,n)};x.useContext=function(e){return C.H.useContext(e)};x.useDebugValue=function(){};x.useDeferredValue=function(e,n){return C.H.useDeferredValue(e,n)};x.useEffect=function(e,n){return C.H.useEffect(e,n)};x.useEffectEvent=function(e){return C.H.useEffectEvent(e)};x.useId=function(){return C.H.useId()};x.useImperativeHandle=function(e,n,t){return C.H.useImperativeHandle(e,n,t)};x.useInsertionEffect=function(e,n){return C.H.useInsertionEffect(e,n)};x.useLayoutEffect=function(e,n){return C.H.useLayoutEffect(e,n)};x.useMemo=function(e,n){return C.H.useMemo(e,n)};x.useOptimistic=function(e,n){return C.H.useOptimistic(e,n)};x.useReducer=function(e,n,t){return C.H.useReducer(e,n,t)};x.useRef=function(e){return C.H.useRef(e)};x.useState=function(e){return C.H.useState(e)};x.useSyncExternalStore=function(e,n,t){return C.H.useSyncExternalStore(e,n,t)};x.useTransition=function(){return C.H.useTransition()};x.version="19.2.7";Ee.exports=x;var V=Ee.exports;const ut=Ce(V);var Re={exports:{}},Ae={},Me={exports:{}},Le={};/**
 * @license React
 * use-sync-external-store-shim.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var R=V;function pt(e,n){return e===n&&(e!==0||1/e===1/n)||e!==e&&n!==n}var ft=typeof Object.is=="function"?Object.is:pt,mt=R.useState,vt=R.useEffect,yt=R.useLayoutEffect,gt=R.useDebugValue;function xt(e,n){var t=n(),o=mt({inst:{value:t,getSnapshot:n}}),r=o[0].inst,s=o[1];return yt(function(){r.value=t,r.getSnapshot=n,B(r)&&s({inst:r})},[e,t,n]),vt(function(){return B(r)&&s({inst:r}),e(function(){B(r)&&s({inst:r})})},[e]),gt(t),t}function B(e){var n=e.getSnapshot;e=e.value;try{var t=n();return!ft(e,t)}catch{return!0}}function ht(e,n){return n()}var bt=typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"?ht:xt;Le.useSyncExternalStore=R.useSyncExternalStore!==void 0?R.useSyncExternalStore:bt;Me.exports=Le;var Ct=Me.exports;/**
 * @license React
 * use-sync-external-store-shim/with-selector.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var F=V,Et=Ct;function wt(e,n){return e===n&&(e!==0||1/e===1/n)||e!==e&&n!==n}var Tt=typeof Object.is=="function"?Object.is:wt,St=Et.useSyncExternalStore,kt=F.useRef,It=F.useEffect,_t=F.useMemo,Rt=F.useDebugValue;Ae.useSyncExternalStoreWithSelector=function(e,n,t,o,r){var s=kt(null);if(s.current===null){var a={hasValue:!1,value:null};s.current=a}else a=s.current;s=_t(function(){function c(y){if(!d){if(d=!0,u=y,y=o(y),r!==void 0&&a.hasValue){var p=a.value;if(r(p,y))return l=p}return l=y}if(p=l,Tt(u,y))return p;var m=o(y);return r!==void 0&&r(p,m)?(u=y,p):(u=y,l=m)}var d=!1,u,l,h=t===void 0?null:t;return[function(){return c(n())},h===null?void 0:function(){return c(h())}]},[n,t,o,r]);var i=St(e,s[0],s[1]);return It(function(){a.hasValue=!0,a.value=i},[i]),Rt(i),i};Re.exports=Ae;var At=Re.exports;const Mt=Ce(At),De={},{useDebugValue:Lt}=ut,{useSyncExternalStoreWithSelector:Dt}=Mt;let re=!1;const Pt=e=>e;function Ot(e,n=Pt,t){(De?"production":void 0)!=="production"&&t&&!re&&(console.warn("[DEPRECATED] Use `createWithEqualityFn` instead of `create` or use `useStoreWithEqualityFn` instead of `useStore`. They can be imported from 'zustand/traditional'. https://github.com/pmndrs/zustand/discussions/1937"),re=!0);const o=Dt(e.subscribe,e.getState,e.getServerState||e.getInitialState,n,t);return Lt(o),o}const zt=e=>{(De?"production":void 0)!=="production"&&typeof e!="function"&&console.warn("[DEPRECATED] Passing a vanilla store will be unsupported in a future version. Instead use `import { useStore } from 'zustand'`.");const n=typeof e=="function"?Xe(e):e,t=(o,r)=>Ot(n,o,r);return Object.assign(t,n),t},S=e=>zt,$={BASE_URL:"/",DEV:!1,MODE:"production",PROD:!0,SSR:!1},J=new Map,z=e=>{const n=J.get(e);return n?Object.fromEntries(Object.entries(n.stores).map(([t,o])=>[t,o.getState()])):{}},$t=(e,n,t)=>{if(e===void 0)return{type:"untracked",connection:n.connect(t)};const o=J.get(t.name);if(o)return{type:"tracked",store:e,...o};const r={connection:n.connect(t),stores:{}};return J.set(t.name,r),{type:"tracked",store:e,...r}},Ft=(e,n={})=>(t,o,r)=>{const{enabled:s,anonymousActionType:a,store:i,...c}=n;let d;try{d=(s??($?"production":void 0)!=="production")&&window.__REDUX_DEVTOOLS_EXTENSION__}catch{}if(!d)return($?"production":void 0)!=="production"&&s&&console.warn("[zustand devtools middleware] Please install/enable Redux devtools extension"),e(t,o,r);const{connection:u,...l}=$t(i,d,c);let h=!0;r.setState=(m,f,v)=>{const g=t(m,f);if(!h)return g;const b=v===void 0?{type:a||"anonymous"}:typeof v=="string"?{type:v}:v;return i===void 0?(u==null||u.send(b,o()),g):(u==null||u.send({...b,type:`${i}/${b.type}`},{...z(c.name),[i]:r.getState()}),g)};const y=(...m)=>{const f=h;h=!1,t(...m),h=f},p=e(r.setState,o,r);if(l.type==="untracked"?u==null||u.init(p):(l.stores[l.store]=r,u==null||u.init(Object.fromEntries(Object.entries(l.stores).map(([m,f])=>[m,m===l.store?p:f.getState()])))),r.dispatchFromDevtools&&typeof r.dispatch=="function"){let m=!1;const f=r.dispatch;r.dispatch=(...v)=>{($?"production":void 0)!=="production"&&v[0].type==="__setState"&&!m&&(console.warn('[zustand devtools middleware] "__setState" action type is reserved to set state from the devtools. Avoid using it.'),m=!0),f(...v)}}return u.subscribe(m=>{var f;switch(m.type){case"ACTION":if(typeof m.payload!="string"){console.error("[zustand devtools middleware] Unsupported action format");return}return U(m.payload,v=>{if(v.type==="__setState"){if(i===void 0){y(v.state);return}Object.keys(v.state).length!==1&&console.error(`
                    [zustand devtools middleware] Unsupported __setState action format. 
                    When using 'store' option in devtools(), the 'state' should have only one key, which is a value of 'store' that was passed in devtools(),
                    and value of this only key should be a state object. Example: { "type": "__setState", "state": { "abc123Store": { "foo": "bar" } } }
                    `);const g=v.state[i];if(g==null)return;JSON.stringify(r.getState())!==JSON.stringify(g)&&y(g);return}r.dispatchFromDevtools&&typeof r.dispatch=="function"&&r.dispatch(v)});case"DISPATCH":switch(m.payload.type){case"RESET":return y(p),i===void 0?u==null?void 0:u.init(r.getState()):u==null?void 0:u.init(z(c.name));case"COMMIT":if(i===void 0){u==null||u.init(r.getState());return}return u==null?void 0:u.init(z(c.name));case"ROLLBACK":return U(m.state,v=>{if(i===void 0){y(v),u==null||u.init(r.getState());return}y(v[i]),u==null||u.init(z(c.name))});case"JUMP_TO_STATE":case"JUMP_TO_ACTION":return U(m.state,v=>{if(i===void 0){y(v);return}JSON.stringify(r.getState())!==JSON.stringify(v[i])&&y(v[i])});case"IMPORT_STATE":{const{nextLiftedState:v}=m.payload,g=(f=v.computedStates.slice(-1)[0])==null?void 0:f.state;if(!g)return;y(i===void 0?g:g[i]),u==null||u.send(null,v);return}case"PAUSE_RECORDING":return h=!h}return}}),p},k=Ft,U=(e,n)=>{let t;try{t=JSON.parse(e)}catch(o){console.error("[zustand devtools middleware] Could not parse the received json",o)}t!==void 0&&n(t)};function Nt(e,n){let t;try{t=e()}catch{return}return{getItem:r=>{var s;const a=c=>c===null?null:JSON.parse(c,void 0),i=(s=t.getItem(r))!=null?s:null;return i instanceof Promise?i.then(a):a(i)},setItem:(r,s)=>t.setItem(r,JSON.stringify(s,void 0)),removeItem:r=>t.removeItem(r)}}const D=e=>n=>{try{const t=e(n);return t instanceof Promise?t:{then(o){return D(o)(t)},catch(o){return this}}}catch(t){return{then(o){return this},catch(o){return D(o)(t)}}}},jt=(e,n)=>(t,o,r)=>{let s={getStorage:()=>localStorage,serialize:JSON.stringify,deserialize:JSON.parse,partialize:f=>f,version:0,merge:(f,v)=>({...v,...f}),...n},a=!1;const i=new Set,c=new Set;let d;try{d=s.getStorage()}catch{}if(!d)return e((...f)=>{console.warn(`[zustand persist middleware] Unable to update item '${s.name}', the given storage is currently unavailable.`),t(...f)},o,r);const u=D(s.serialize),l=()=>{const f=s.partialize({...o()});let v;const g=u({state:f,version:s.version}).then(b=>d.setItem(s.name,b)).catch(b=>{v=b});if(v)throw v;return g},h=r.setState;r.setState=(f,v)=>{h(f,v),l()};const y=e((...f)=>{t(...f),l()},o,r);let p;const m=()=>{var f;if(!d)return;a=!1,i.forEach(g=>g(o()));const v=((f=s.onRehydrateStorage)==null?void 0:f.call(s,o()))||void 0;return D(d.getItem.bind(d))(s.name).then(g=>{if(g)return s.deserialize(g)}).then(g=>{if(g)if(typeof g.version=="number"&&g.version!==s.version){if(s.migrate)return s.migrate(g.state,g.version);console.error("State loaded from storage couldn't be migrated since no migrate function was provided")}else return g.state}).then(g=>{var b;return p=s.merge(g,(b=o())!=null?b:y),t(p,!0),l()}).then(()=>{v==null||v(p,void 0),a=!0,c.forEach(g=>g(p))}).catch(g=>{v==null||v(void 0,g)})};return r.persist={setOptions:f=>{s={...s,...f},f.getStorage&&(d=f.getStorage())},clearStorage:()=>{d==null||d.removeItem(s.name)},getOptions:()=>s,rehydrate:()=>m(),hasHydrated:()=>a,onHydrate:f=>(i.add(f),()=>{i.delete(f)}),onFinishHydration:f=>(c.add(f),()=>{c.delete(f)})},m(),p||y},Ht=(e,n)=>(t,o,r)=>{let s={storage:Nt(()=>localStorage),partialize:m=>m,version:0,merge:(m,f)=>({...f,...m}),...n},a=!1;const i=new Set,c=new Set;let d=s.storage;if(!d)return e((...m)=>{console.warn(`[zustand persist middleware] Unable to update item '${s.name}', the given storage is currently unavailable.`),t(...m)},o,r);const u=()=>{const m=s.partialize({...o()});return d.setItem(s.name,{state:m,version:s.version})},l=r.setState;r.setState=(m,f)=>{l(m,f),u()};const h=e((...m)=>{t(...m),u()},o,r);r.getInitialState=()=>h;let y;const p=()=>{var m,f;if(!d)return;a=!1,i.forEach(g=>{var b;return g((b=o())!=null?b:h)});const v=((f=s.onRehydrateStorage)==null?void 0:f.call(s,(m=o())!=null?m:h))||void 0;return D(d.getItem.bind(d))(s.name).then(g=>{if(g)if(typeof g.version=="number"&&g.version!==s.version){if(s.migrate)return[!0,s.migrate(g.state,g.version)];console.error("State loaded from storage couldn't be migrated since no migrate function was provided")}else return[!1,g.state];return[!1,void 0]}).then(g=>{var b;const[I,L]=g;if(y=s.merge(L,(b=o())!=null?b:h),t(y,!0),I)return u()}).then(()=>{v==null||v(y,void 0),y=o(),a=!0,c.forEach(g=>g(y))}).catch(g=>{v==null||v(void 0,g)})};return r.persist={setOptions:m=>{s={...s,...m},m.storage&&(d=m.storage)},clearStorage:()=>{d==null||d.removeItem(s.name)},getOptions:()=>s,rehydrate:()=>p(),hasHydrated:()=>a,onHydrate:m=>(i.add(m),()=>{i.delete(m)}),onFinishHydration:m=>(c.add(m),()=>{c.delete(m)})},s.skipHydration||p(),y||h},Bt=(e,n)=>"getStorage"in n||"serialize"in n||"deserialize"in n?(($?"production":void 0)!=="production"&&console.warn("[DEPRECATED] `getStorage`, `serialize` and `deserialize` options are deprecated. Use `storage` option instead."),jt(e,n)):Ht(e,n),M=Bt;let Ut=0;S()(k(e=>({toasts:[],addToast:n=>{const t=`toast-${Ut++}`,o=n.duration||3e3;return e(r=>({toasts:[...r.toasts,{...n,id:t}]})),o>0&&setTimeout(()=>{e(r=>({toasts:r.toasts.filter(s=>s.id!==t)}))},o),t},removeToast:n=>e(t=>({toasts:t.toasts.filter(o=>o.id!==n)})),clearToasts:()=>e({toasts:[]}),showSettingsModal:!1,showCommandPalette:!1,showDiffViewer:!1,showWritePanel:!1,showBatchPanel:!1,setSettingsModal:n=>e({showSettingsModal:n}),setCommandPalette:n=>e({showCommandPalette:n}),setDiffViewer:n=>e({showDiffViewer:n}),setWritePanel:n=>e({showWritePanel:n}),setBatchPanel:n=>e({showBatchPanel:n}),sidebarCollapsed:!1,showContextPanel:!0,setSidebarCollapsed:n=>e({sidebarCollapsed:n}),setContextPanel:n=>e({showContextPanel:n}),theme:"dark",setTheme:n=>{e({theme:n}),document.documentElement.setAttribute("data-theme",n),localStorage.setItem("devforge-theme",n)}}),{name:"UIStore"}));S()(k(M((e,n)=>({conversations:[],currentConversationId:null,isLoading:!1,currentInput:"",createConversation:t=>{const o=`conv-${Date.now()}`,r={id:o,title:t,messages:[],createdAt:new Date,updatedAt:new Date};return e(s=>({conversations:[...s.conversations,r],currentConversationId:o})),o},deleteConversation:t=>e(o=>({conversations:o.conversations.filter(r=>r.id!==t),currentConversationId:o.currentConversationId===t?null:o.currentConversationId})),setCurrentConversation:t=>e({currentConversationId:t,currentInput:""}),addMessage:(t,o)=>e(r=>({conversations:r.conversations.map(s=>s.id===t?{...s,messages:[...s.messages,o],updatedAt:new Date}:s)})),removeMessage:(t,o)=>e(r=>({conversations:r.conversations.map(s=>s.id===t?{...s,messages:s.messages.filter(a=>a.id!==o),updatedAt:new Date}:s)})),clearMessages:t=>e(o=>({conversations:o.conversations.map(r=>r.id===t?{...r,messages:[],updatedAt:new Date}:r)})),setCurrentInput:t=>e({currentInput:t}),setLoading:t=>e({isLoading:t}),getCurrentConversation:()=>{const t=n();return t.conversations.find(o=>o.id===t.currentConversationId)},getConversationMessages:t=>{const r=n().conversations.find(s=>s.id===t);return(r==null?void 0:r.messages)||[]},getTotalTokens:t=>{const r=n().conversations.find(s=>s.id===t);return(r==null?void 0:r.messages.reduce((s,a)=>s+(a.tokens||0),0))||0}}),{name:"chat-store",version:1}),{name:"ChatStore"}));S()(k(M((e,n)=>({repositories:[],currentRepoId:null,fileTree:[],selectedFileId:null,openFiles:[],searchQuery:"",filteredFiles:[],addRepository:t=>e(o=>({repositories:[...o.repositories,t],currentRepoId:o.currentRepoId||t.id})),removeRepository:t=>e(o=>({repositories:o.repositories.filter(r=>r.id!==t),currentRepoId:o.currentRepoId===t?null:o.currentRepoId})),setCurrentRepository:t=>e({currentRepoId:t}),setFileTree:t=>e({fileTree:t}),selectFile:t=>e({selectedFileId:t}),openFile:t=>e(o=>({openFiles:o.openFiles.includes(t)?o.openFiles:[...o.openFiles,t],selectedFileId:t})),closeFile:t=>e(o=>({openFiles:o.openFiles.filter(r=>r!==t),selectedFileId:o.selectedFileId===t?null:o.selectedFileId})),toggleFolder:t=>{const o=r=>r.map(s=>s.id===t?{...s,isOpen:!s.isOpen}:s.children?{...s,children:o(s.children)}:s);e(r=>({fileTree:o(r.fileTree)}))},setSearchQuery:t=>{e(o=>({searchQuery:t,filteredFiles:n().searchFiles(t)}))},searchFiles:t=>{if(!t)return[];const o=r=>r.flatMap(s=>{const a=s.name.toLowerCase().includes(t.toLowerCase()),i=s.children?o(s.children):[];return a?[{...s,children:i}]:i});return o(n().fileTree)},getCurrentRepository:()=>{const t=n();return t.repositories.find(o=>o.id===t.currentRepoId)},getFile:t=>{const o=r=>{for(const s of r){if(s.id===t)return s;if(s.children){const a=o(s.children);if(a)return a}}};return o(n().fileTree)},getOpenFileCount:()=>n().openFiles.length}),{name:"repo-store",version:1}),{name:"RepoStore"}));S()(k(M((e,n)=>({providers:[],activeProviderId:null,models:[],activeModelId:null,temperature:.7,maxTokens:2e3,topP:1,topK:0,featureFlags:{canaryDeployment:!1,betaFeatures:!1,autoSave:!0,diffViewer:!0,batchOperations:!0},addProvider:t=>e(o=>({providers:[...o.providers,t],activeProviderId:o.activeProviderId||t.id})),updateProvider:(t,o)=>e(r=>({providers:r.providers.map(s=>s.id===t?{...s,...o}:s)})),removeProvider:t=>e(o=>({providers:o.providers.filter(r=>r.id!==t),activeProviderId:o.activeProviderId===t?null:o.activeProviderId})),setActiveProvider:t=>e({activeProviderId:t}),addModel:t=>e(o=>({models:[...o.models,t],activeModelId:o.activeModelId||t.id})),updateModel:(t,o)=>e(r=>({models:r.models.map(s=>s.id===t?{...s,...o}:s)})),removeModel:t=>e(o=>({models:o.models.filter(r=>r.id!==t),activeModelId:o.activeModelId===t?null:o.activeModelId})),setActiveModel:t=>e({activeModelId:t}),updateSettings:t=>e(t),setFeatureFlag:(t,o)=>e(r=>({featureFlags:{...r.featureFlags,[t]:o}})),toggleFeatureFlag:t=>e(o=>({featureFlags:{...o.featureFlags,[t]:!o.featureFlags[t]}})),isFeatureEnabled:t=>n().featureFlags[t]||!1,getActiveProvider:()=>{const t=n();return t.providers.find(o=>o.id===t.activeProviderId)},getActiveModel:()=>{const t=n();return t.models.find(o=>o.id===t.activeModelId)},getProviderModels:t=>n().models.filter(r=>r.provider===t),isConfigurationValid:()=>{var s,a;const t=n(),o=(s=t.getActiveProvider)==null?void 0:s.call(t),r=(a=t.getActiveModel)==null?void 0:a.call(t);return!!(o!=null&&o.isConfigured&&r)}}),{name:"config-store",version:1}),{name:"ConfigStore"}));S()(k(M((e,n)=>({files:[],totalTokens:0,maxTokens:8e3,references:[],createdAt:new Date,lastUpdated:new Date,addFile:t=>e(o=>{const r=o.totalTokens+t.tokens;return r>o.maxTokens?(console.warn("Adding file would exceed token limit"),o):{files:[...o.files,t],totalTokens:r,lastUpdated:new Date}}),removeFile:t=>e(o=>{const r=o.files.find(s=>s.id===t);return{files:o.files.filter(s=>s.id!==t),totalTokens:o.totalTokens-((r==null?void 0:r.tokens)||0),lastUpdated:new Date}}),updateFile:(t,o)=>e(r=>{const s=r.files.find(c=>c.id===t);if(!s)return r;const a=(o.tokens||s.tokens)-s.tokens,i=r.totalTokens+a;return i>r.maxTokens?(console.warn("Updating file would exceed token limit"),r):{files:r.files.map(c=>c.id===t?{...c,...o}:c),totalTokens:i,lastUpdated:new Date}}),clearFiles:()=>e({files:[],totalTokens:0,lastUpdated:new Date}),addReference:t=>e(o=>({references:[...o.references,t],lastUpdated:new Date})),removeReference:t=>e(o=>({references:o.references.filter(r=>r.id!==t),lastUpdated:new Date})),clearReferences:()=>e({references:[],lastUpdated:new Date}),setMaxTokens:t=>e({maxTokens:t}),getAvailableTokens:()=>{const t=n();return t.maxTokens-t.totalTokens},canAddFile:t=>{const o=n();return o.totalTokens+t<=o.maxTokens},getContextSize:()=>n().files.length,getTokenUsage:()=>n().totalTokens,getTokenPercentage:()=>{const t=n();return t.totalTokens/t.maxTokens*100},hasRoom:t=>{const o=n();return o.totalTokens+t<=o.maxTokens}}),{name:"context-store",version:1}),{name:"ContextStore"}));S()(k(M((e,n)=>({memories:[],conversationMemories:[],recentContext:[],maxRecentContext:20,addMemory:t=>{const o=`mem-${Date.now()}`,r=new Date;return e(s=>({memories:[...s.memories,{...t,id:o,createdAt:r,updatedAt:r}]})),o},updateMemory:(t,o)=>e(r=>({memories:r.memories.map(s=>s.id===t?{...s,...o,updatedAt:new Date}:s)})),removeMemory:t=>e(o=>({memories:o.memories.filter(r=>r.id!==t)})),getMemory:t=>n().memories.find(r=>r.key===t),saveConversationMemory:t=>e(o=>o.conversationMemories.find(s=>s.conversationId===t.conversationId)?{conversationMemories:o.conversationMemories.map(s=>s.conversationId===t.conversationId?{...t,createdAt:s.createdAt,updatedAt:new Date}:s)}:{conversationMemories:[...o.conversationMemories,{...t,createdAt:new Date,updatedAt:new Date}]}),removeConversationMemory:t=>e(o=>({conversationMemories:o.conversationMemories.filter(r=>r.conversationId!==t)})),getConversationMemory:t=>n().conversationMemories.find(r=>r.conversationId===t),addToRecentContext:t=>e(o=>({recentContext:[t,...o.recentContext].slice(0,o.maxRecentContext)})),getRecentContext:()=>n().recentContext,clearRecentContext:()=>e({recentContext:[]}),getMemoriesByCategory:t=>n().memories.filter(r=>r.category===t),getAllMemories:()=>n().memories,getMemorySize:()=>{const t=n();return t.memories.length+t.conversationMemories.length}}),{name:"memory-store",version:1}),{name:"MemoryStore"}));S()(k(M((e,n)=>({dailyMetrics:[],modelStats:[],totalMessages:0,totalTokens:0,totalCost:0,periodStart:new Date(Date.now()-30*24*60*60*1e3),periodEnd:new Date,recordUsage:t=>e(o=>({dailyMetrics:[...o.dailyMetrics,{...t,timestamp:new Date}],totalMessages:o.totalMessages+t.messagesCount,totalTokens:o.totalTokens+t.tokensUsed,totalCost:o.totalCost+t.cost})),updateModelStats:(t,o,r,s)=>e(a=>a.modelStats.find(c=>c.model===t)?{modelStats:a.modelStats.map(c=>c.model===t?{...c,totalMessages:c.totalMessages+1,totalTokens:c.totalTokens+r,totalCost:c.totalCost+s,lastUsed:new Date}:c)}:{modelStats:[...a.modelStats,{model:t,provider:o,totalMessages:1,totalTokens:r,totalCost:s,lastUsed:new Date}]}),clearStats:()=>e({dailyMetrics:[],modelStats:[],totalMessages:0,totalTokens:0,totalCost:0}),setPeriod:(t,o)=>e({periodStart:t,periodEnd:o}),getDailyMetrics:()=>n().dailyMetrics,getMetricsForPeriod:(t,o)=>n().dailyMetrics.filter(s=>s.timestamp>=t&&s.timestamp<=o),getModelStats:()=>n().modelStats.sort((o,r)=>r.totalCost-o.totalCost),getTopModel:()=>n().modelStats.reduce((o,r)=>!o||r.totalCost>o.totalCost?r:o),getTotalCost:()=>n().totalCost,getAverageTokensPerMessage:()=>{const t=n();return t.totalMessages>0?Math.round(t.totalTokens/t.totalMessages):0}}),{name:"stats-store",version:1}),{name:"StatsStore"}));window.lastClickedButton=null;window.lastInputValue="";window.dialogConfirmed=!1;const Y=document.getElementById("toast-container"),E=w.createContainer();Y&&(Y.parentNode.replaceChild(E,Y),E.id="toast-container",E.setAttribute("data-testid","toast-container"));const se=document.getElementById("notification-hub-container"),P=Je.create();se&&se.appendChild(P);const Yt=e=>{e.querySelectorAll("input").forEach(t=>{t.style.cssText=`
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background-color: var(--input-bg);
            color: var(--text);
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
            width: 200px;
          `,t.addEventListener("focus",()=>{t.style.borderColor="var(--accent)",t.style.boxShadow="0 0 0 2px var(--accent-dim)"}),t.addEventListener("blur",()=>{t.style.borderColor="var(--border)",t.style.boxShadow="none"}),t.addEventListener("input",o=>{window.lastInputValue=o.target.value})})},Wt=e=>{e.querySelectorAll("button").forEach(t=>{if(t.id&&t.id.startsWith("btn-")){t.style.cssText=`
              padding: 8px 16px;
              border-radius: 6px;
              border: none;
              cursor: pointer;
              font-size: 14px;
              font-weight: 500;
              transition: background-color 0.2s, color 0.2s, border-color 0.2s;
              opacity: 1;
              font-family: inherit;
            `;const o=t.getAttribute("data-variant")||"primary",r={primary:`
                background-color: var(--accent);
                color: var(--bg);
              `,secondary:`
                background-color: var(--panel);
                color: var(--text);
                border: 1px solid var(--border);
              `,danger:`
                background-color: var(--red);
                color: white;
              `};t.style.cssText+=r[o],t.addEventListener("mouseenter",()=>{t.style.opacity="0.8"}),t.addEventListener("mouseleave",()=>{t.style.opacity="1"}),t.addEventListener("click",()=>{window.lastClickedButton=t.textContent})}})};Wt(document);Yt(document);var ae;(ae=document.getElementById("btn-success-toast"))==null||ae.addEventListener("click",()=>{const e=w.create({id:"success-"+Date.now(),text:"Operation completed successfully!",type:"success",duration:3e3,onRemove:n=>{var t;(t=document.getElementById(n))==null||t.remove()}});E.appendChild(e)});var ie;(ie=document.getElementById("btn-error-toast"))==null||ie.addEventListener("click",()=>{const e=w.create({id:"error-"+Date.now(),text:"An error occurred. Please try again.",type:"error",duration:3e3,onRemove:n=>{var t;(t=document.getElementById(n))==null||t.remove()}});E.appendChild(e)});var ce;(ce=document.getElementById("btn-info-toast"))==null||ce.addEventListener("click",()=>{const e=w.create({id:"info-"+Date.now(),text:"Here is some useful information.",type:"info",duration:3e3,onRemove:n=>{var t;(t=document.getElementById(n))==null||t.remove()}});E.appendChild(e)});var le;(le=document.getElementById("btn-warning-toast"))==null||le.addEventListener("click",()=>{const e=w.create({id:"warning-"+Date.now(),text:"Warning: This action requires attention.",type:"warning",duration:3e3,onRemove:n=>{var t;(t=document.getElementById(n))==null||t.remove()}});E.appendChild(e)});var de;(de=document.getElementById("btn-success-notif"))==null||de.addEventListener("click",()=>{P.success("Success","Operation completed successfully!")});var ue;(ue=document.getElementById("btn-error-notif"))==null||ue.addEventListener("click",()=>{P.error("Error","An error occurred. Please try again.")});var pe;(pe=document.getElementById("btn-info-notif"))==null||pe.addEventListener("click",()=>{P.info("Info","Here is some useful information.")});var fe;(fe=document.getElementById("btn-warning-notif"))==null||fe.addEventListener("click",()=>{P.warning("Warning","Warning: This action requires attention.")});var me;(me=document.getElementById("btn-confirm-dialog"))==null||me.addEventListener("click",()=>{const e=be.create({title:"Confirm Action",message:"Are you sure you want to proceed with this action?",confirmText:"Confirm",cancelText:"Cancel",type:"confirm",onConfirm:()=>{window.dialogConfirmed=!0;const n=w.create({id:"confirm-"+Date.now(),text:"Action confirmed!",type:"success",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)},onCancel:()=>{const n=w.create({id:"cancel-"+Date.now(),text:"Action cancelled.",type:"info",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}});document.body.appendChild(e)});var ve;(ve=document.getElementById("btn-alert-dialog"))==null||ve.addEventListener("click",()=>{const e=be.create({title:"Alert",message:"This is an important alert message.",confirmText:"OK",type:"alert",onConfirm:()=>{const n=w.create({id:"alert-"+Date.now(),text:"Alert acknowledged!",type:"info",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}});document.body.appendChild(e)});const T=document.getElementById("layout-container");var ye;(ye=document.getElementById("btn-sidebar"))==null||ye.addEventListener("click",()=>{if(T){T.innerHTML="";const e=Fe.create();T.appendChild(e)}});var ge;(ge=document.getElementById("btn-main-panel"))==null||ge.addEventListener("click",()=>{if(T){T.innerHTML="";const e=je.create();T.appendChild(e)}});var xe;(xe=document.getElementById("btn-settings-panel"))==null||xe.addEventListener("click",()=>{if(T){T.innerHTML="";const e=Be.create();T.appendChild(e)}});var he;(he=document.getElementById("btn-command-palette"))==null||he.addEventListener("click",()=>{const e=Ye.create({commands:[{id:"cmd-new-chat",label:"New Chat",description:"Start a new conversation",category:"Chat",icon:"💬",onSelect:()=>{const n=w.create({id:"cmd-"+Date.now(),text:"New chat started!",type:"success",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}},{id:"cmd-open-file",label:"Open File",description:"Open a file from repository",category:"File",icon:"📁",onSelect:()=>{const n=w.create({id:"cmd-"+Date.now(),text:"File dialog opened",type:"info",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}},{id:"cmd-settings",label:"Settings",description:"Open settings",category:"General",icon:"⚙️",onSelect:()=>{const n=w.create({id:"cmd-"+Date.now(),text:"Settings opened",type:"info",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}},{id:"cmd-search",label:"Search",description:"Search in repository",category:"File",icon:"🔍",onSelect:()=>{const n=w.create({id:"cmd-"+Date.now(),text:"Search initiated",type:"info",duration:3e3,onRemove:t=>{var o;(o=document.getElementById(t))==null||o.remove()}});E.appendChild(n)}}],onClose:()=>{}});document.body.appendChild(e)});
//# sourceMappingURL=index-CgvJuv7b.js.map
