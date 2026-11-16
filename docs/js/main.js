// CIP — interazioni: menu a tutto schermo, carousel, torna su, fade d'ingresso
(() => {
  const menu = document.getElementById('menu');
  const apri = document.querySelector('.header__menu');
  const chiudi = menu?.querySelector('.menu__chiudi');
  const set = (aperto) => {
    menu.classList.toggle('aperto', aperto);
    document.body.classList.toggle('menu-aperto', aperto);
    apri.setAttribute('aria-expanded', aperto);
    menu.setAttribute('aria-hidden', !aperto);
    if (aperto) chiudi.focus(); else apri.focus();
  };
  apri?.addEventListener('click', () => set(true));
  chiudi?.addEventListener('click', () => set(false));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && menu.classList.contains('aperto')) set(false); });

  // Carousel: frecce scorrono di una card
  document.querySelectorAll('.carosello').forEach((c) => {
    const t = c.querySelector('.carosello__traccia');
    const passo = () => (t.querySelector('.card')?.offsetWidth || 300) + 40;
    c.querySelector('.carosello__freccia--prev')?.addEventListener('click', () => {
      t.scrollBy({ left: t.scrollLeft <= 5 ? t.scrollWidth : -passo(), behavior: 'smooth' });
    });
    c.querySelector('.carosello__freccia--next')?.addEventListener('click', () => {
      const fine = t.scrollLeft + t.clientWidth >= t.scrollWidth - 5;
      t.scrollBy({ left: fine ? -t.scrollWidth : passo(), behavior: 'smooth' });
    });
  });

  // Torna su
  const su = document.querySelector('.su');
  if (su) addEventListener('scroll', () => su.classList.toggle('visibile', scrollY > 500), { passive: true });

  // Hero: zoom legato allo scroll (Motion FX Elementor: 1.2 → 1)
  const hero = document.querySelector('.hero');
  const hc = hero?.querySelector('.hero__contenuto');
  if (hc && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const zoom = () => {
      const k = Math.max(0, 1 - scrollY / hero.offsetHeight);
      hc.style.transform = `scale(${(1 + 0.2 * k * k).toFixed(4)})`;
    };
    zoom(); addEventListener('scroll', zoom, { passive: true });
  }

  // Fade d'ingresso
  const io = new IntersectionObserver((voci) => voci.forEach((v) => {
    if (v.isIntersecting) { v.target.classList.add('visto'); io.unobserve(v.target); }
  }), { threshold: 0.15 });
  document.querySelectorAll('.fade').forEach((el) => io.observe(el));
})();
