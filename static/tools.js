/* Trade-specific customer tools for the demo sites. Each tool ends in a real action:
   it hands a pre-written message to the live receptionist chat (window.askFromTool). */
(function () {
  const gbp = n => '£' + Math.round(n).toLocaleString('en-GB');
  // kind "triage": pick a situation -> safe advice, urgency, and a message for the receptionist.
  // kind "estimate": a few inputs -> a guide price range -> a quote request.
  const T = {
    electrician: { kind: 'triage', icon: 'electrician', title: 'What is your electrics doing?', sub: 'Pick the closest match. You get safe next steps now, and we get the details.',
      opts: [
        ['Sparks, burning smell or scorched socket', 'urgent', 'Switch off at the consumer unit if you can do it safely, and keep away from the socket. Don\u2019t use water on electrical burning.', 'There are sparks or a burning smell from a socket'],
        ['Fuse box keeps tripping', 'soon', 'Unplug everything on that circuit, reset the switch, then plug things back one at a time. If it trips with nothing plugged in, leave it off.', 'My fuse box keeps tripping'],
        ['No power in part of the house', 'soon', 'Check the consumer unit for a switch in the down position and reset it once. Ask a neighbour if their power is off too.', 'I have no power in part of the house'],
        ['Lights flickering', 'routine', 'Try a new bulb first. If several lights flicker together, note when it happens so the electrician can trace it.', 'My lights keep flickering'],
        ['I need an EICR or landlord certificate', 'routine', 'Have the property address and a rough age of the wiring handy. Most EICRs take 2 to 4 hours.', 'I need an EICR safety certificate'],
      ] },
    plumber: { kind: 'triage', icon: 'plumber', title: 'Where is the water coming from?', sub: 'Stop the damage first, then we\u2019ll sort the rest.',
      opts: [
        ['A burst or gushing pipe', 'urgent', 'Turn the stopcock clockwise to shut off the water. It\u2019s usually under the kitchen sink. Switch off the electrics near the water, then open cold taps to drain.', 'A pipe has burst and water is everywhere'],
        ['Leaking under the sink', 'soon', 'Put a bowl under it and close the small isolation valve on the pipe with a flat screwdriver (quarter turn).', 'There\u2019s a leak under my sink'],
        ['Toilet won\u2019t stop running or is blocked', 'soon', 'Don\u2019t keep flushing. Close the isolation valve on the cistern pipe if the water is rising.', 'My toilet is blocked or keeps running'],
        ['Dripping tap', 'routine', 'Usually a washer or cartridge. A photo of the tap helps us bring the right part.', 'I have a dripping tap that needs fixing'],
        ['Water through the ceiling', 'urgent', 'Shut off the water at the stopcock and switch off the lights below. Don\u2019t stand under a bulging ceiling.', 'Water is coming through my ceiling'],
      ] },
    heating: { kind: 'triage', icon: 'heating', title: 'Boiler showing a fault code?', sub: 'Pick the code on the display. Some you can clear yourself in a minute.',
      opts: [
        ['I can smell gas', 'urgent', 'Leave the property, don\u2019t touch switches, and ring the National Gas Emergency line on 0800 111 999 now. Then tell us so we can follow up.', 'I can smell gas'],
        ['Low pressure (Worcester EA / CE, Vaillant F22, Baxi E119)', 'routine', 'Check the gauge. If it\u2019s under 1 bar, top it up to about 1.5 with the filling loop under the boiler, then reset. If it keeps dropping, there\u2019s a leak to find.', 'My boiler pressure is low and showing a fault code'],
        ['Ignition failure (Worcester EA, Vaillant F28 or F29, Baxi E133)', 'soon', 'Check the gas is on at the meter and other gas appliances work. Press reset once. If it locks out again, leave it.', 'My boiler has an ignition fault'],
        ['Frozen condensate pipe (cold snap, gurgling)', 'soon', 'Pour warm (not boiling) water along the white plastic pipe outside, then reset the boiler.', 'I think my condensate pipe is frozen'],
        ['No heating or hot water, no code', 'soon', 'Check the thermostat and timer, and that the boiler has power. Note any noises or lights.', 'I have no heating or hot water'],
      ] },
    locksmith: { kind: 'estimate', icon: 'locksmith', title: 'Locked out? See your price before we come', sub: 'Fixed callout pricing. No surprises at the door.',
      inputs: [['When', 'sel', [['Daytime (8am to 6pm)', 0], ['Evening (6pm to midnight)', 25], ['Overnight (midnight to 8am)', 45]]],
               ['Door', 'sel', [['uPVC or composite front door', 0], ['Wooden door, mortice lock', 15], ['Car or van', 30]]],
               ['Need a new lock?', 'sel', [['No, just get me in', 0], ['Yes, replace the lock', 65], ['Yes, anti-snap upgrade', 95]]]],
      calc: v => [79 + v[0] + v[1] + v[2], 99 + v[0] + v[1] + v[2]],
      msg: (r, l) => `I'm locked out (${l.join(', ')}). Your price shows ${r}. Can someone come?`, note: 'Most callouts within 30 to 60 minutes. ID and proof of address needed.' },
    beauty: { kind: 'estimate', icon: 'beauty', title: 'Build your appointment', sub: 'See the time and price before you book. Patch tests flagged for you.',
      inputs: [['Treatment', 'sel', [['Gel manicure', 32], ['Lash lift and tint', 45], ['Brow lamination', 40], ['Full face makeup', 55]]],
               ['Add on', 'sel', [['Nothing extra', 0], ['Nail art (2 nails)', 6], ['Brow tint', 12], ['Gel removal', 8]]]],
      calc: v => [v[0] + v[1], v[0] + v[1]],
      msg: (r, l) => `I'd like to book ${l.filter(x => !/^Nothing/.test(x)).join(' + ')} (${r}).`,
      extra: l => /lash|tint/i.test(l.join(' ')) ? 'Needs a patch test 48 hours before. We\u2019ll book that for you too.' : 'No patch test needed for this one.' },
    barber: { kind: 'slots', icon: 'barber', title: 'Today\u2019s chair', sub: 'Pick a free slot and it\u2019s held while you confirm.',
      services: [['Skin fade', 22, 30], ['Scissor cut', 20, 30], ['Beard trim and line-up', 12, 15], ['Kids cut (under 12)', 15, 20]] },
    dogwalker: { kind: 'estimate', icon: 'dogwalker', title: 'Plan your dog\u2019s week', sub: 'See your weekly price, then pick days.',
      inputs: [['Dogs', 'sel', [['1 dog', 1], ['2 dogs', 1.6], ['3 dogs', 2.1]]],
               ['Walk', 'sel', [['Group walk (1 hour)', 15], ['Solo walk (1 hour)', 20], ['Puppy visit (30 min)', 12]]],
               ['Days a week', 'sel', [['2 days', 2], ['3 days', 3], ['5 days', 5]]]],
      calc: v => { const w = v[0] * v[1] * v[2]; return [w, w]; },
      msg: (r, l) => `I'd like regular walks: ${l.join(', ')} (about ${r} a week). Can we arrange a meet and greet?`, note: 'Free meet and greet first. Insured, DBS checked, GPS updates after every walk.' },
    msp: { kind: 'triage', icon: 'msp', title: 'Raise a ticket in 10 seconds', sub: 'Pick the impact. Priority 1 pages the on-call engineer immediately.',
      opts: [
        ['Whole office down or ransomware message', 'urgent', 'Priority 1: response within 15 minutes. If you see a ransom note, unplug affected machines from the network but don\u2019t switch them off.', 'Priority 1: the whole office is down'],
        ['I clicked a suspicious link', 'urgent', 'Priority 1: disconnect from Wi-Fi, don\u2019t enter any passwords, and keep the email. We\u2019ll reset your credentials.', 'I clicked a phishing link'],
        ['One person can\u2019t work', 'soon', 'Priority 2: response within 1 hour. Try a restart and note any error message.', 'One of my staff can\u2019t log in or work'],
        ['New starter or leaver', 'routine', 'Priority 3: give us 2 working days for laptops and accounts.', 'I need a new starter set up'],
        ['Printer or small niggle', 'routine', 'Priority 4: next working day. A photo of any error helps.', 'Our printer won\u2019t connect'],
      ] },
    soletrader: { kind: 'triage', icon: 'soletrader', title: 'What do you need?', sub: 'Pick one and we\u2019ll ask only what we need.',
      opts: [
        ['Something\u2019s broken and it\u2019s urgent', 'urgent', 'Make it safe if you can, and tell us the address and what\u2019s happened.', 'It\u2019s urgent, can someone come tonight?'],
        ['A quote for a job', 'routine', 'A couple of photos and rough measurements get you a faster, more accurate quote.', 'Can you give me a quote?'],
        ['Book a visit', 'routine', 'Tell us the job and a couple of days that suit you.', 'I\u2019d like to book a visit'],
      ] },
  };
  const LV = { urgent: ['Urgent', 'Alerting the on-call team now'], soon: ['Soon', 'Today or tomorrow'], routine: ['Routine', 'Book a time that suits you'] };

  window.renderTradeTool = function (el, trade, prices) {
    const t = T[trade] || T.soletrader;
    const head = `<div class="tt-hd"><span class="tt-ic">${icon(t.icon, 18)}</span><div><h3>${t.title}</h3><p>${t.sub}</p></div></div>`;
    if (t.kind === 'triage') {
      el.innerHTML = head + `<div class="tt-opts">${t.opts.map((o, i) => `<button class="tt-opt" data-i="${i}"><span class="lv ${o[1]}"></span>${o[0]}</button>`).join('')}</div><div class="tt-out" hidden></div>`;
      const out = el.querySelector('.tt-out');
      el.querySelectorAll('.tt-opt').forEach(b => b.onclick = () => {
        el.querySelectorAll('.tt-opt').forEach(x => x.classList.toggle('on', x === b));
        const o = t.opts[+b.dataset.i], L = LV[o[1]];
        out.hidden = false;
        out.innerHTML = `<div class="tt-badge ${o[1]}">${L[0]} \u00b7 ${L[1]}</div><p>${o[2]}</p><button class="b pri sm">${o[1] === 'urgent' ? 'Alert them now' : 'Send this to us'}</button>`;
        out.querySelector('button').onclick = () => window.askFromTool(o[3]);
      });
    } else if (t.kind === 'estimate') {
      el.innerHTML = head + `<div class="tt-grid">${t.inputs.map((inp, i) => `<label class="f">${inp[0]}<select data-i="${i}">${inp[2].map((o, j) => `<option value="${j}">${o[0]}</option>`).join('')}</select></label>`).join('')}</div>
        <div class="tt-total"><div><small>Guide price</small><b class="tt-p"></b><span class="tt-x"></span></div><button class="b pri sm">Request this</button></div>${t.note ? `<p class="tt-note">${t.note}</p>` : ''}`;
      const sels = [...el.querySelectorAll('select')];
      const upd = () => {
        const v = sels.map((s, i) => t.inputs[i][2][s.value][1]), lab = sels.map((s, i) => t.inputs[i][2][s.value][0]);
        const [a, b] = t.calc(v), r = a === b ? gbp(a) : `${gbp(a)} to ${gbp(b)}`;
        el.querySelector('.tt-p').textContent = r;
        el.querySelector('.tt-x').textContent = t.extra ? t.extra(lab) : '';
        el.querySelector('.tt-total button').onclick = () => window.askFromTool(t.msg(r, lab));
      };
      sels.forEach(s => s.onchange = upd); upd();
    } else if (t.kind === 'slots') {
      const now = new Date(), slots = [];
      for (let h = 9; h < 19; h++) for (const m of [0, 30]) {
        const d = new Date(now); d.setHours(h, m, 0, 0);
        const seed = (h * 7 + m + now.getDate()) % 5;
        slots.push([`${String(h).padStart(2, '0')}:${m ? '30' : '00'}`, d > now && seed > 1]);
      }
      el.innerHTML = head + `<div class="tt-grid"><label class="f">Service<select>${t.services.map((s, i) => `<option value="${i}">${s[0]} \u00b7 \u00a3${s[1]} \u00b7 ${s[2]} min</option>`).join('')}</select></label></div>
        <div class="tt-slots">${slots.map(([s, ok]) => `<button class="slot${ok ? '' : ' off'}" ${ok ? '' : 'disabled'}>${s}</button>`).join('')}</div>
        ${slots.some(s => s[1]) ? '' : '<p class="tt-note">Fully booked for today. Ask for tomorrow\u2019s first slot.</p>'}`;
      const sel = el.querySelector('select');
      el.querySelectorAll('.slot:not(.off)').forEach(b => b.onclick = () => {
        const s = t.services[sel.value];
        window.askFromTool(`Can I book a ${s[0].toLowerCase()} today at ${b.textContent}?`);
      });
    }
  };
})();
