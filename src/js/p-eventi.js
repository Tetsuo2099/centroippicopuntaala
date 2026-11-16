// CIP — Eventi: calendario mensile (griglia lun–dom, mese corrente, frecce prev/next)
(() => {
  const cal = document.querySelector('[data-cal]');
  if (!cal) return;
  const titolo = cal.querySelector('.cal__titolo');
  const corpo = cal.querySelector('tbody');
  const oggi = new Date();
  let m = new Date(oggi.getFullYear(), oggi.getMonth(), 1);
  const nomi = new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric' });

  const disegna = () => {
    titolo.textContent = nomi.format(m);
    const primo = (m.getDay() + 6) % 7; // lunedì = 0
    const giorni = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
    const righe = Math.ceil((primo + giorni) / 7);
    let h = '';
    for (let r = 0; r < righe; r++) {
      h += '<tr>';
      for (let c = 0; c < 7; c++) {
        const n = r * 7 + c - primo + 1;
        if (n < 1 || n > giorni) { h += '<td class="fuori"></td>'; continue; }
        const o = n === oggi.getDate() && m.getMonth() === oggi.getMonth() && m.getFullYear() === oggi.getFullYear();
        h += `<td${o ? ' class="oggi" aria-current="date"' : ''}><span class="cal__num">${n}</span></td>`;
      }
      h += '</tr>';
    }
    corpo.innerHTML = h;
  };
  cal.querySelector('.cal__nav--prev').addEventListener('click', () => { m = new Date(m.getFullYear(), m.getMonth() - 1, 1); disegna(); });
  cal.querySelector('.cal__nav--next').addEventListener('click', () => { m = new Date(m.getFullYear(), m.getMonth() + 1, 1); disegna(); });
  disegna();
})();
