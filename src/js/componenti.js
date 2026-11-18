// CIP — componenti: galleria a striscia (autoplay) + lightbox accessibile + video di sfondo
(() => {
  const EN = document.documentElement.lang === 'en';
  const ridotto = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Video di sfondo: con "riduci movimento" restano fermi sul poster
  if (ridotto) document.querySelectorAll('video[data-sfondo]').forEach((v) => { v.removeAttribute('autoplay'); v.pause(); });

  // ---- Galleria: autoplay 5s (pausa su hover/focus), loop ----
  document.querySelectorAll('.galleria').forEach((g) => {
    const t = g.querySelector('.galleria__traccia');
    if (!t || ridotto) return;
    let ferma = false;
    g.addEventListener('mouseenter', () => (ferma = true));
    g.addEventListener('mouseleave', () => (ferma = false));
    g.addEventListener('focusin', () => (ferma = true));
    g.addEventListener('focusout', () => (ferma = false));
    setInterval(() => {
      if (ferma || document.hidden || document.body.classList.contains('lb-aperto')) return;
      const passo = t.firstElementChild.offsetWidth;
      const fine = t.scrollLeft + t.clientWidth >= t.scrollWidth - 5;
      t.scrollTo({ left: fine ? 0 : t.scrollLeft + passo, behavior: 'smooth' });
    }, 5000);
  });

  // ---- Photo-scroller: frecce scorrono di ~un'immagine ----
  document.querySelectorAll('.scroller').forEach((s) => {
    const t = s.querySelector('.scroller__traccia');
    s.querySelector('.scroller__freccia--prev')?.addEventListener('click', () => t.scrollBy({ left: -t.clientWidth * 0.6, behavior: ridotto ? 'auto' : 'smooth' }));
    s.querySelector('.scroller__freccia--next')?.addEventListener('click', () => t.scrollBy({ left: t.clientWidth * 0.6, behavior: ridotto ? 'auto' : 'smooth' }));
  });

  // ---- Lightbox: link [data-lb] raggruppati per [data-lb-gruppo] ----
  let lb, img, num, voci = [], i = 0, ultimo = null;
  const crea = () => {
    lb = document.createElement('div');
    lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', EN ? 'Image gallery' : 'Galleria immagini');
    lb.innerHTML = `<button type="button" class="lb__x" aria-label="${EN ? 'Close' : 'Chiudi'}">&times;</button>` +
      `<button type="button" class="lb__prev" aria-label="${EN ? 'Previous image' : 'Immagine precedente'}">&#8249;</button>` +
      `<img class="lb__img" alt=""><button type="button" class="lb__next" aria-label="${EN ? 'Next image' : 'Immagine successiva'}">&#8250;</button><div class="lb__n" aria-live="polite"></div>`;
    document.body.appendChild(lb);
    img = lb.querySelector('.lb__img'); num = lb.querySelector('.lb__n');
    lb.querySelector('.lb__x').onclick = chiudi;
    lb.querySelector('.lb__prev').onclick = (e) => { e.stopPropagation(); vai(i - 1); };
    lb.querySelector('.lb__next').onclick = (e) => { e.stopPropagation(); vai(i + 1); };
    lb.addEventListener('click', (e) => { if (e.target === lb || e.target === img) chiudi(); });
    document.addEventListener('keydown', (e) => {
      if (!lb.classList.contains('aperto')) return;
      if (e.key === 'Escape') chiudi();
      else if (e.key === 'ArrowLeft') vai(i - 1);
      else if (e.key === 'ArrowRight') vai(i + 1);
      else if (e.key === 'Tab') { // focus intrappolato nelle 3 frecce/pulsanti
        const b = [...lb.querySelectorAll('button')]; const k = b.indexOf(document.activeElement);
        e.preventDefault(); b[(k + (e.shiftKey ? -1 : 1) + b.length) % b.length].focus();
      }
    });
    let x0 = null;
    lb.addEventListener('touchstart', (e) => (x0 = e.touches[0].clientX), { passive: true });
    lb.addEventListener('touchend', (e) => { if (x0 === null) return; const d = e.changedTouches[0].clientX - x0; if (Math.abs(d) > 50) vai(i + (d < 0 ? 1 : -1)); x0 = null; });
  };
  const vai = (n) => {
    i = (n + voci.length) % voci.length;
    const a = voci[i];
    img.src = a.href; img.alt = a.querySelector('img')?.alt || '';
    num.textContent = `${i + 1} / ${voci.length}`;
  };
  const chiudi = () => { lb.classList.remove('aperto'); document.body.classList.remove('lb-aperto'); ultimo?.focus(); };
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[data-lb]');
    if (!a) return;
    e.preventDefault();
    if (!lb) crea();
    const gr = a.closest('[data-lb-gruppo]') || document;
    voci = [...gr.querySelectorAll('a[data-lb]')];
    ultimo = a;
    lb.classList.add('aperto'); document.body.classList.add('lb-aperto');
    vai(voci.indexOf(a));
    lb.querySelector('.lb__x').focus();
  });

  // ---- Form Web3Forms: invio via fetch (se fallisce, resta l'invio normale del form) ----
  document.querySelectorAll('form[data-web3]').forEach((f) => {
    const stato = f.querySelector('.form__stato');
    const btn = f.querySelector('.form__invia');
    f.addEventListener('submit', async (e) => {
      if (f.querySelector('[name=access_key]').value.startsWith('WEB3FORMS_KEY')) return; // chiave non ancora inserita: invio nativo
      e.preventDefault();
      btn.disabled = true; stato.className = 'form__stato'; stato.textContent = EN ? 'Sending…' : 'Invio in corso…';
      try {
        const r = await fetch(f.action, { method: 'POST', headers: { Accept: 'application/json' }, body: new FormData(f) });
        const d = await r.json();
        if (!d.success) throw new Error(d.message);
        f.reset(); stato.textContent = f.dataset.ok || (EN ? 'Thank you! Your message has been sent.' : 'Grazie! Il tuo messaggio è stato inviato.');
      } catch (_) {
        stato.className = 'form__stato errore';
        stato.textContent = EN ? 'Sorry, the form could not be sent. Please try again or email us at cippuntaala@gmail.com.' : 'Non è stato possibile inviare il modulo. Riprova o scrivici a cippuntaala@gmail.com.';
      }
      btn.disabled = false;
    });
  });
})();
