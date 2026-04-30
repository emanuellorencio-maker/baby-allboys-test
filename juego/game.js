(() => {
  "use strict";

  const canvas = document.getElementById("game-canvas");
  const ctx = canvas.getContext("2d");
  const startScreen = document.getElementById("start-screen");
  const overScreen = document.getElementById("game-over-screen");
  const playButton = document.getElementById("play-button");
  const retryButton = document.getElementById("retry-button");
  const shareButton = document.getElementById("share-button");
  const pauseButton = document.getElementById("pause-button");
  const pauseBadge = document.getElementById("pause-badge");
  const shareFallback = document.getElementById("share-fallback");
  const scoreEl = document.getElementById("score");
  const coinsEl = document.getElementById("coins");
  const comboEl = document.getElementById("combo");
  const bestEl = document.getElementById("best");
  const finalScoreEl = document.getElementById("final-score");
  const finalBestEl = document.getElementById("final-best");
  const losePhraseEl = document.getElementById("lose-phrase");

  const ASSETS = {
    player: "assets/jugador.svg",
    platform1: "assets/plataforma.svg",
    platform2: "assets/plataforma2.svg",
    platform3: "assets/plataforma3.svg",
    background: "assets/fondo-tribuna.svg",
    cone: "assets/cono.svg",
    rival: "assets/rival.svg",
    coin: "assets/moneda.svg",
    boot: "assets/botin.svg",
    flag: "assets/bandera.svg"
  };

  const LOSE_PHRASES = [
    "Te falto potrero",
    "Una mas y sale",
    "Casi llegas a Primera",
    "Dale Albo, no aflojes",
    "El baby no perdona"
  ];

  const images = {};
  const state = {
    mode: "start",
    width: 360,
    height: 640,
    dpr: 1,
    cameraY: 0,
    score: 0,
    best: Number(localStorage.getItem("babyAlboJumpBest") || 0),
    coins: 0,
    combo: 1,
    comboTimer: 0,
    difficulty: 1,
    touchX: null,
    touchActive: false,
    touchHoldUntil: 0,
    inputX: 0,
    screenShake: 0,
    keys: { left: false, right: false },
    platforms: [],
    collectibles: [],
    obstacles: [],
    particles: [],
    popups: [],
    highestY: 0,
    lastTime: 0,
    spawnY: 0,
    player: null,
    startLockUntil: 0
  };

  bestEl.textContent = state.best;

  function loadImages() {
    return Promise.all(Object.entries(ASSETS).map(([key, src]) => new Promise((resolve) => {
      const img = new Image();
      img.onload = resolve;
      img.onerror = resolve;
      img.src = src;
      images[key] = img;
    })));
  }

  function resize() {
    const ratio = 9 / 16;
    let w = window.innerWidth;
    let h = window.innerHeight;
    if (w / h > ratio) w = h * ratio;
    state.width = Math.floor(w);
    state.height = Math.floor(h);
    state.dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(state.width * state.dpr);
    canvas.height = Math.floor(state.height * state.dpr);
    canvas.style.width = `${state.width}px`;
    canvas.style.height = `${state.height}px`;
    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
  }

  function rand(min, max) {
    return min + Math.random() * (max - min);
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function vibrate(ms = 22) {
    if (navigator.vibrate) navigator.vibrate(ms);
  }

  function startGame() {
    if (state.mode === "playing") return;
    const w = state.width;
    const h = state.height;
    state.mode = "playing";
    state.cameraY = 0;
    state.score = 0;
    state.coins = 0;
    state.combo = 1;
    state.comboTimer = 0;
    state.difficulty = 1;
    state.highestY = 0;
    state.spawnY = h - 80;
    state.touchX = null;
    state.touchActive = false;
    state.touchHoldUntil = 0;
    state.inputX = 0;
    state.screenShake = 0;
    state.particles = [];
    state.popups = [];
    state.platforms = [];
    state.collectibles = [];
    state.obstacles = [];
    state.player = {
      x: w * .5 - 29,
      y: h - 150,
      w: 58,
      h: 70,
      vx: 0,
      vy: -14.8,
      facing: 1,
      boost: 0,
      squash: 0
    };

    state.platforms.push(makePlatform(w * .5 - 62, h - 58, 124, "base", 1));
    while (state.spawnY > -h * 3) spawnPlatform();
    startScreen.classList.add("hidden");
    overScreen.classList.add("hidden");
    pauseButton.classList.remove("hidden");
    pauseButton.textContent = "II";
    pauseBadge.classList.add("hidden");
    shareFallback.classList.add("hidden");
    updateHud();
  }

  function makePlatform(x, y, width, type, variant) {
    return {
      x,
      y,
      w: width,
      h: 30,
      type,
      variant,
      phase: rand(0, 100),
      squash: 0
    };
  }

  function spawnPlatform() {
    const altitude = Math.max(0, -state.spawnY);
    const ramp = Math.min(1, altitude / 3600);
    const gap = rand(78 + ramp * 18, 112 + ramp * 58 + state.difficulty * 10);
    state.spawnY -= gap;
    const platformWidth = Math.max(72, 124 - ramp * 34 - state.difficulty * 3);
    const x = rand(14, state.width - platformWidth - 14);
    const movingChance = Math.min(.48, .1 + ramp * .3 + state.difficulty * .03);
    const type = Math.random() < movingChance ? "moving" : "normal";
    const variant = 1 + Math.floor(Math.random() * 3);
    const platform = makePlatform(x, state.spawnY, platformWidth, type, variant);
    state.platforms.push(platform);

    if (Math.random() < .46) {
      state.collectibles.push({ kind: "coin", x: x + platformWidth * .5 - 16, y: platform.y - 46, w: 32, h: 32, taken: false, spin: rand(0, 6) });
    } else if (Math.random() < .12) {
      state.collectibles.push({ kind: "boot", x: x + platformWidth * .5 - 18, y: platform.y - 50, w: 36, h: 36, taken: false, spin: 0 });
    }

    const obstacleChance = Math.min(.36, .05 + ramp * .2 + state.difficulty * .025);
    if (altitude > 850 && Math.random() < obstacleChance) {
      const rival = Math.random() < .6;
      state.obstacles.push({
        kind: rival ? "rival" : "cone",
        x: rand(18, state.width - 58),
        y: platform.y - rand(84, 165),
        w: rival ? 54 : 38,
        h: rival ? 58 : 48,
        phase: rand(0, 100)
      });
    }
  }

  function updateHud() {
    scoreEl.textContent = state.score;
    coinsEl.textContent = state.coins;
    comboEl.textContent = `x${state.combo}`;
    bestEl.textContent = state.best;
  }

  function jump(strength = 14.2, platform = null) {
    const p = state.player;
    p.vy = -strength - Math.min(2.4, state.difficulty * .14);
    p.squash = .2;
    if (platform) platform.squash = .24;
    burst(p.x + p.w / 2, p.y + p.h, "#ffffff", 18, 1.15);
  }

  function burst(x, y, color, count, power = 1) {
    for (let i = 0; i < count; i += 1) {
      state.particles.push({
        x,
        y,
        vx: rand(-3.1, 3.1) * power,
        vy: rand(-5.4, -.7) * power,
        life: rand(.34, .74),
        max: .74,
        color,
        size: rand(2.8, 6.5)
      });
    }
  }

  function popup(text, x, y, color = "#f4c84a") {
    state.popups.push({ text, x, y, life: .9, color });
  }

  function rectsOverlap(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function update(dt) {
    if (state.mode !== "playing") {
      updateEffects(dt);
      return;
    }

    const p = state.player;
    state.difficulty = 1 + Math.min(5, state.score / 720);
    state.comboTimer = Math.max(0, state.comboTimer - dt);
    if (state.comboTimer <= 0) state.combo = 1;

    let target = 0;
    const touchHeld = state.touchActive || performance.now() < state.touchHoldUntil;
    if (touchHeld && state.touchX !== null) {
      const center = p.x + p.w / 2;
      target = clamp((state.touchX - center) / (state.width * .28), -1, 1);
    }
    if (state.keys.left) target -= 1;
    if (state.keys.right) target += 1;
    state.inputX += (clamp(target, -1, 1) - state.inputX) * Math.min(1, dt * 13);

    const maxSpeed = 7.8 + Math.min(1.35, state.difficulty * .16);
    p.vx += state.inputX * 37 * dt;
    p.vx *= Math.pow(.015, dt);
    p.vx = clamp(p.vx, -maxSpeed, maxSpeed);
    p.x += p.vx * 60 * dt;
    p.vy += (28.6 + state.difficulty * .55) * dt;
    p.y += p.vy * 60 * dt;
    p.squash = Math.max(0, p.squash - dt * 2.6);
    if (Math.abs(p.vx) > .18) p.facing = Math.sign(p.vx);

    if (p.x > state.width + 18) p.x = -p.w;
    if (p.x < -p.w - 18) p.x = state.width;

    for (const platform of state.platforms) {
      platform.squash = Math.max(0, platform.squash - dt * 2.7);
      if (platform.type === "moving") {
        platform.x += Math.sin(performance.now() / 650 + platform.phase) * (.42 + state.difficulty * .07);
        platform.x = clamp(platform.x, 8, state.width - platform.w - 8);
      }
      const falling = p.vy > 0;
      const feet = p.y + p.h;
      const previousFeet = feet - p.vy * 60 * dt;
      if (falling && previousFeet <= platform.y + 8 && feet >= platform.y && p.x + p.w * .76 > platform.x && p.x + p.w * .24 < platform.x + platform.w) {
        p.y = platform.y - p.h;
        jump(p.boost > 0 ? 16.5 : 14.3, platform);
      }
    }

    for (const item of state.collectibles) {
      if (item.taken) continue;
      item.spin += dt * 7.5;
      if (rectsOverlap(p, item)) {
        item.taken = true;
        if (item.kind === "coin") {
          state.combo = state.comboTimer > 0 ? Math.min(9, state.combo + 1) : 1;
          state.comboTimer = 2.2;
          const gain = 20 + state.combo * 8;
          state.coins += 1;
          state.score += gain;
          burst(item.x + item.w / 2, item.y + item.h / 2, "#f4c84a", 20, 1.2);
          popup(`+${gain} x${state.combo}`, item.x - 5, item.y);
        } else {
          p.boost = 4.5;
          jump(17.2);
          burst(item.x + item.w / 2, item.y + item.h / 2, "#39b66a", 22, 1.25);
          popup("BOTIN!", item.x - 8, item.y, "#39b66a");
        }
        vibrate(18);
      }
    }

    p.boost = Math.max(0, p.boost - dt);

    for (const obstacle of state.obstacles) {
      obstacle.x += obstacle.kind === "rival" ? Math.sin(performance.now() / 560 + obstacle.phase) * (.72 + state.difficulty * .03) : 0;
      if (rectsOverlap({ x: p.x + 9, y: p.y + 8, w: p.w - 18, h: p.h - 14 }, obstacle)) {
        endGame();
        return;
      }
    }

    const desiredCamera = Math.min(state.cameraY, p.y - state.height * .42);
    state.cameraY += (desiredCamera - state.cameraY) * Math.min(1, dt * 5.6);
    state.highestY = Math.min(state.highestY, p.y);
    state.score = Math.max(state.score, Math.floor(-state.highestY * .2));

    while (state.spawnY > state.cameraY - state.height * 1.35) spawnPlatform();
    const cleanupY = state.cameraY + state.height + 170;
    state.platforms = state.platforms.filter((o) => o.y < cleanupY);
    state.collectibles = state.collectibles.filter((o) => !o.taken && o.y < cleanupY);
    state.obstacles = state.obstacles.filter((o) => o.y < cleanupY);

    updateEffects(dt);
    if (p.y - state.cameraY > state.height + 120) endGame();
    updateHud();
  }

  function updateEffects(dt) {
    state.screenShake = Math.max(0, state.screenShake - dt * 12);
    state.particles.forEach((part) => {
      part.life -= dt;
      part.x += part.vx * 60 * dt;
      part.y += part.vy * 60 * dt;
      part.vy += 8 * dt;
    });
    state.particles = state.particles.filter((part) => part.life > 0);
    state.popups.forEach((pop) => {
      pop.life -= dt;
      pop.y -= 38 * dt;
    });
    state.popups = state.popups.filter((pop) => pop.life > 0);
  }

  function endGame() {
    state.mode = "over";
    state.screenShake = 1;
    state.touchActive = false;
    state.touchX = null;
    vibrate(55);
    state.best = Math.max(state.best, state.score);
    localStorage.setItem("babyAlboJumpBest", String(state.best));
    losePhraseEl.textContent = LOSE_PHRASES[Math.floor(Math.random() * LOSE_PHRASES.length)];
    finalScoreEl.textContent = state.score;
    finalBestEl.textContent = state.best;
    pauseButton.classList.add("hidden");
    pauseBadge.classList.add("hidden");
    updateHud();
    overScreen.classList.remove("hidden");
  }

  function togglePause(event) {
    if (event) event.preventDefault();
    if (state.mode === "playing") {
      state.mode = "paused";
      pauseButton.textContent = ">";
      pauseBadge.classList.remove("hidden");
    } else if (state.mode === "paused") {
      state.mode = "playing";
      pauseButton.textContent = "II";
      pauseBadge.classList.add("hidden");
    }
  }

  function draw() {
    const shakeX = state.screenShake ? rand(-5, 5) * state.screenShake : 0;
    const shakeY = state.screenShake ? rand(-4, 4) * state.screenShake : 0;
    ctx.clearRect(0, 0, state.width, state.height);
    ctx.save();
    ctx.translate(shakeX, shakeY);
    drawBackground();
    ctx.save();
    ctx.translate(0, -state.cameraY);
    drawWorld();
    ctx.restore();
    drawEffects();
    if (state.screenShake > .01) {
      ctx.fillStyle = `rgba(255,255,255,${state.screenShake * .16})`;
      ctx.fillRect(0, 0, state.width, state.height);
    }
    ctx.restore();
  }

  function drawBackground() {
    const bg = images.background;
    if (bg?.complete) ctx.drawImage(bg, 0, 0, state.width, state.height);
    const t = performance.now() / 1000;
    ctx.fillStyle = "rgba(0,0,0,.08)";
    ctx.fillRect(0, 0, state.width, state.height);

    ctx.save();
    ctx.globalAlpha = .18;
    ctx.fillStyle = "#ffffff";
    for (let i = 0; i < 4; i += 1) {
      const y = 120 + i * 145 + Math.sin(t + i) * 12;
      const x = (i % 2 ? state.width * .68 : state.width * .28) + Math.sin(t * .45 + i) * 28;
      ctx.beginPath();
      ctx.ellipse(x, y + ((-state.cameraY * .08) % 80), 86, 24, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    drawFlag(22, 104 + Math.sin(t * 1.4) * 7, 56, Math.sin(t * 2) * .05);
    drawFlag(state.width - 78, 162 + Math.sin(t * 1.2) * 7, 58, Math.sin(t * 2.2) * -.05);

    ctx.fillStyle = "rgba(255,255,255,.08)";
    for (let y = 80; y < state.height; y += 110) {
      ctx.fillRect(0, y + ((-state.cameraY * .18) % 110), state.width, 1);
    }
  }

  function drawFlag(x, y, size, rotation) {
    const img = images.flag;
    ctx.save();
    ctx.translate(x + size / 2, y);
    ctx.rotate(rotation);
    if (img?.complete && img.naturalWidth) ctx.drawImage(img, -size / 2, 0, size, size * .76);
    ctx.restore();
  }

  function drawWorld() {
    for (const platform of state.platforms) {
      const img = images[`platform${platform.variant}`] || images.platform1;
      const scaleY = 1 - platform.squash * .28;
      ctx.save();
      ctx.translate(platform.x + platform.w / 2, platform.y + platform.h / 2);
      ctx.scale(1 + platform.squash * .08, scaleY);
      drawImage(img, -platform.w / 2, -platform.h / 2, platform.w, platform.h);
      ctx.restore();
      if (platform.type === "moving") {
        ctx.fillStyle = "rgba(255,255,255,.78)";
        ctx.fillRect(platform.x + 16, platform.y + 3, platform.w - 32, 3);
      }
    }

    for (const item of state.collectibles) {
      const bounce = Math.sin(item.spin) * 4;
      drawImage(images[item.kind === "coin" ? "coin" : "boot"], item.x, item.y + bounce, item.w, item.h);
    }

    for (const obstacle of state.obstacles) {
      drawImage(images[obstacle.kind], obstacle.x, obstacle.y, obstacle.w, obstacle.h);
    }

    const p = state.player;
    if (p) {
      ctx.save();
      const cx = p.x + p.w / 2;
      const squashX = 1 + p.squash * .22;
      const squashY = 1 - p.squash * .18;
      ctx.translate(cx, p.y + p.h);
      ctx.scale(p.facing * squashX, squashY);
      drawImage(images.player, -p.w / 2, -p.h, p.w, p.h);
      if (p.boost > 0) {
        ctx.globalAlpha = .78;
        ctx.fillStyle = "#39b66a";
        ctx.beginPath();
        ctx.ellipse(0, 7, 20, 7, 0, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }
  }

  function drawImage(img, x, y, w, h) {
    if (img?.complete && img.naturalWidth) {
      ctx.drawImage(img, x, y, w, h);
    } else {
      ctx.fillStyle = "#fff";
      ctx.fillRect(x, y, w, h);
    }
  }

  function drawEffects() {
    ctx.save();
    ctx.translate(0, -state.cameraY);
    for (const part of state.particles) {
      ctx.globalAlpha = Math.max(0, part.life / part.max);
      ctx.fillStyle = part.color;
      ctx.beginPath();
      ctx.arc(part.x, part.y, part.size, 0, Math.PI * 2);
      ctx.fill();
    }
    for (const pop of state.popups) {
      ctx.globalAlpha = Math.max(0, pop.life / .9);
      ctx.fillStyle = pop.color;
      ctx.font = "900 18px Arial";
      ctx.strokeStyle = "#050505";
      ctx.lineWidth = 4;
      ctx.strokeText(pop.text, pop.x, pop.y);
      ctx.fillText(pop.text, pop.x, pop.y);
    }
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  function loop(time) {
    const dt = Math.min(.033, (time - state.lastTime) / 1000 || .016);
    state.lastTime = time;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  function setTouch(x) {
    const rect = canvas.getBoundingClientRect();
    state.touchX = x - rect.left;
    state.touchActive = true;
    state.touchHoldUntil = performance.now() + 340;
  }

  function clearTouch() {
    state.touchActive = false;
  }

  function handleStart(event) {
    if (event) event.preventDefault();
    const now = performance.now();
    if (now < state.startLockUntil || state.mode === "playing") return;
    state.startLockUntil = now + 350;
    startGame();
  }

  function handleCanvasTouchStart(event) {
    if (state.mode !== "playing") return;
    event.preventDefault();
    if (event.touches[0]) setTouch(event.touches[0].clientX);
  }

  function handleCanvasTouchMove(event) {
    if (state.mode !== "playing") return;
    event.preventDefault();
    if (event.touches[0]) setTouch(event.touches[0].clientX);
  }

  canvas.addEventListener("touchstart", handleCanvasTouchStart, { passive: false });
  canvas.addEventListener("touchmove", handleCanvasTouchMove, { passive: false });
  canvas.addEventListener("touchend", clearTouch);
  canvas.addEventListener("touchcancel", clearTouch);

  canvas.addEventListener("pointerdown", (event) => {
    if (state.mode === "playing") setTouch(event.clientX);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (state.mode === "playing" && (event.pressure || event.buttons)) setTouch(event.clientX);
  });
  canvas.addEventListener("pointerup", clearTouch);
  canvas.addEventListener("pointercancel", clearTouch);

  window.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") state.keys.left = true;
    if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") state.keys.right = true;
    if (event.key.toLowerCase() === "p") togglePause(event);
  });

  window.addEventListener("keyup", (event) => {
    if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") state.keys.left = false;
    if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") state.keys.right = false;
  });

  playButton.addEventListener("click", handleStart);
  playButton.addEventListener("touchend", handleStart, { passive: false });
  retryButton.addEventListener("click", handleStart);
  retryButton.addEventListener("touchend", handleStart, { passive: false });
  pauseButton.addEventListener("click", togglePause);
  pauseButton.addEventListener("touchend", togglePause, { passive: false });

  shareButton.addEventListener("click", async () => {
    const text = `Mi record en Baby Albo Jump es ${state.best} puntos. Lo superas?`;
    shareFallback.classList.add("hidden");
    if (navigator.share) {
      try {
        await navigator.share({ title: "Baby Albo Jump", text, url: location.href });
        return;
      } catch (error) {
        if (error.name === "AbortError") return;
      }
    }
    shareFallback.textContent = text;
    shareFallback.classList.remove("hidden");
  });

  window.addEventListener("resize", resize);
  window.addEventListener("orientationchange", resize);
  document.addEventListener("gesturestart", (event) => event.preventDefault());

  loadImages().then(() => {
    resize();
    requestAnimationFrame(loop);
  });
})();
