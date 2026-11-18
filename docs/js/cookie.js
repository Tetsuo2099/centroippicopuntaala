// Consenso cookie (GDPR): il Meta Pixel parte SOLO dopo "Accetta" o consenso marketing.
// Scelta salvata in localStorage 'cip-consenso' = {marketing:bool, data:ISO}. Riaperto da [data-cookie-preferenze].
(() => {
  const EN = document.documentElement.lang === 'en';
  const CHIAVE = 'cip-consenso', PIXEL_ID = '2933320600326318', DURATA_GIORNI = 180;
  const leggi = () => {
    try {
      const v = JSON.parse(localStorage.getItem(CHIAVE));
      if (v && (Date.now() - new Date(v.data)) / 864e5 < DURATA_GIORNI) return v;
    } catch (e) {}
    return null;
  };
  const salva = (marketing) => {
    try { localStorage.setItem(CHIAVE, JSON.stringify({ marketing, data: new Date().toISOString() })); } catch (e) {}
    if (marketing) pixel();
  };
  let pixelCaricato = false;
  function pixel() {
    if (pixelCaricato) return; pixelCaricato = true;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;
    s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', PIXEL_ID); fbq('track', 'PageView');
  }

  const banner = document.createElement('div');
  banner.className = 'cookie';
  banner.setAttribute('role', 'dialog');
  banner.setAttribute('aria-label', EN ? 'Cookie preferences' : 'Preferenze cookie');
  banner.innerHTML = `
    <div class="cookie__in">
      <p>${EN ? `We use technical cookies that are necessary for the website to work and, only with your consent, marketing cookies (Meta Pixel) to measure how effective our communication is. You can change your mind at any time from "Cookie preferences" at the bottom of the page. <a href="/cookie-policy/" hreflang="it">Cookie policy</a>` : `Usiamo cookie tecnici necessari al funzionamento del sito e, solo con il tuo consenso, cookie di marketing (Meta Pixel) per misurare l'efficacia delle nostre comunicazioni. Puoi cambiare idea in qualsiasi momento da "Preferenze cookie" in fondo alla pagina. <a href="/cookie-policy/">Cookie policy</a>`}</p>
      <div class="cookie__dettaglio" hidden>
        <label><input type="checkbox" checked disabled> ${EN ? 'Necessary — always active' : 'Necessari — sempre attivi'}</label>
        <label><input type="checkbox" class="cookie__mkt"> Marketing — Meta Pixel</label>
      </div>
      <div class="cookie__azioni">
        <button type="button" class="cookie__btn cookie__btn--link" data-az="preferenze">${EN ? 'Preferences' : 'Preferenze'}</button>
        <button type="button" class="cookie__btn" data-az="rifiuta">${EN ? 'Reject' : 'Rifiuta'}</button>
        <button type="button" class="cookie__btn cookie__btn--pieno" data-az="accetta">${EN ? 'Accept' : 'Accetta'}</button>
      </div>
    </div>`;
  const apri = () => {
    const c = leggi();
    banner.querySelector('.cookie__mkt').checked = !!(c && c.marketing);
    document.body.appendChild(banner);
    requestAnimationFrame(() => banner.classList.add('aperto'));
  };
  const chiudi = () => { banner.classList.remove('aperto'); setTimeout(() => banner.remove(), 300); };
  banner.addEventListener('click', (e) => {
    const az = e.target.closest('[data-az]')?.dataset.az;
    if (!az) return;
    const det = banner.querySelector('.cookie__dettaglio');
    if (az === 'preferenze') {
      if (det.hidden) { det.hidden = false; e.target.textContent = EN ? 'Save choice' : 'Salva scelta'; return; }
      salva(banner.querySelector('.cookie__mkt').checked);
    } else salva(az === 'accetta');
    chiudi();
  });
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-cookie-preferenze]')) { e.preventDefault(); apri(); }
  });

  const c = leggi();
  if (!c) apri(); else if (c.marketing) pixel();
})();
