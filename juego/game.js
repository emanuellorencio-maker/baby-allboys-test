(() => {
  "use strict";

  const canvas = document.getElementById("game-canvas");
  const ctx = canvas.getContext("2d");
  const startScreen = document.getElementById("start-screen");
  const overScreen = document.getElementById("game-over-screen");
  const playButton = document.getElementById("play-button");
  const retryButton = document.getElementById("retry-button");
  const shareButton = document.getElementById("share-button");
  const shareFallback = document.getElementById("share-fallback");
  const scoreEl = document.getElementById("score");
  const coinsEl = document.getElementById("coins");
  const bestEl = document.getElementById("best");
  const finalScoreEl = document.getElementById("final-score");
  const finalBestEl = document.getElementById("final-best");

  const ASSETS = {
    player: "assets/jugador.svg",
    platform: "assets/plataforma.svg",
    background: "assets/fondo-tribuna.svg",
    cone: "assets/cono.svg",
    rival: "assets/rival.svg",
    coin: "assets/moneda.svg",
    boot: "assets/botin.svg",
    flag: "assets/bandera.svg"
  };

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
    difficulty: 1,
    touchX: null,
    keys: { left: false, right: false },
    platforms: [],
    collectibles: [],
    obstacles: [],
    particles: [],
    popups: [],
    highestY: 0,
    lastTime: 0,
    spawnY: 0,
    player: null
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

  function vibrate(ms = 22) {
    if (navigator.vibrate) navigator.vibrate(ms);
  }

  function startGame() {
    const w = state.width;
    const h = state.height;
    if (state.mode === "playing") return;
    state.mode = "playing";
    state.cameraY = 0;
    state.score = 0;
    state.coins = 0;
    state.difficulty = 1;
    state.highestY = 0;
    state.spawnY = h - 80;
    state.particles = [];
    state.popups = [];
    state.platforms = [];
    state.collectibles = [];
    state.obstacles = [];
    state.player = {
      x: w * .5 - 28,
      y: h - 150,
      w: 56,
      h: 66,
      vx: 0,
      vy: -13.5,
      facing: 1,
      boost: 0
    };

    state.platforms.push({ x: w * .5 - 58, y: h - 64, w: 116, h: 30, type: "base" });
    while (state.spawnY > -h * 3) spawnPlatform();
    startScreen.classList.add("hidden");
    overScreen.classList.add("hidden");
    shareFallback.classList.add("hidden");
    updateHud();
  }

  function spawnPlatform() {
    const gap = rand(76, 118 + state.difficulty * 8);
    state.spawnY -= gap;
    const platformWidth = Math.max(76, 118 - state.difficulty * 4);
    const x = rand(16, state.width - platformWidth - 16);
    const platform = { x, y: state.spawnY, w: platformWidth, h: 30, type: Math.random() < .18 ? "moving" : "normal", phase: rand(0, 100) };
    state.platforms.push(platform);

    if (Math.random() < .42) {
      state.collectibles.push({ kind: "coin", x: x + platformWidth * .5 - 16, y: platform.y - 44, w: 32, h: 32, taken: false, spin: rand(0, 6) });
    } else if (Math.random() < .12) {
      state.collectibles.push({ kind: "boot", x: x + platformWidth * .5 - 18, y: platform.y - 48, w: 36, h: 36, taken: false, spin: 0 });
    }

    if (state.score > 180 && Math.random() < Math.min(.26, .08 + state.difficulty * .025)) {
      const rival = Math.random() < .55;
      state.obstacles.push({
        kind: rival ? "rival" : "cone",
        x: rand(18, state.width - 58),
        y: platform.y - rand(84, 150),
        w: rival ? 54 : 38,
        h: rival ? 58 : 48,
        phase: rand(0, 100)
      });
    }
  }

  function updateHud() {
    scoreEl.textContent = state.score;
    coinsEl.textContent = state.coins;
    bestEl.textContent = state.best;
  }

  function jump(strength = 13.8) {
    state.player.vy = -strength - Math.min(2.2, state.difficulty * .12);
    burst(state.player.x + state.player.w / 2, state.player.y + state.player.h, "#ffffff", 10);
  }

  function burst(x, y, color, count) {
    for (let i = 0; i < count; i += 1) {
      state.particles.push({
        x,
        y,
        vx: rand(-2.2, 2.2),
        vy: rand(-3.8, -.5),
        life: rand(.25, .55),
        max: .55,
        color,
        size: rand(2, 5)
      });
    }
  }

  function popup(text, x, y, color = "#f4c84a") {
    state.popups.push({ text, x, y, life: .8, color });
  }

  function rectsOverlap(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function update(dt) {
    if (state.mode !== "playing") return;
    const p = state.player;
    state.difficulty = 1 + Math.floor(state.score / 450) * .35;

    let target = 0;
    if (state.touchX !== null) {
      const center = p.x + p.w / 2;
      target = Math.max(-1, Math.min(1, (state.touchX - center) / (state.width * .24)));
    }
    if (state.keys.left) target -= 1;
    if (state.keys.right) target += 1;

    p.vx += target * 38 * dt;
    p.vx *= Math.pow(.0015, dt);
    p.vx = Math.max(-8.2, Math.min(8.2, p.vx));
    p.x += p.vx * 60 * dt;
    p.vy += 31 * dt;
    p.y += p.vy * 60 * dt;
    if (Math.abs(p.vx) > .2) p.facing = Math.sign(p.vx);

    if (p.x > state.width + 16) p.x = -p.w;
    if (p.x < -p.w - 16) p.x = state.width;

    for (const platform of state.platforms) {
      if (platform.type === "moving") {
        platform.x += Math.sin(performance.now() / 700 + platform.phase) * .28 * state.difficulty;
        platform.x = Math.max(8, Math.min(state.width - platform.w - 8, platform.x));
      }
      const falling = p.vy > 0;
      const feet = p.y + p.h;
      const previousFeet = feet - p.vy * 60 * dt;
      if (falling && previousFeet <= platform.y + 8 && feet >= platform.y && p.x + p.w * .76 > platform.x && p.x + p.w * .24 < platform.x + platform.w) {
        p.y = platform.y - p.h;
        jump(p.boost > 0 ? 16.2 : 13.8);
      }
    }

    for (const item of state.collectibles) {
      if (item.taken) continue;
      item.spin += dt * 7;
      if (rectsOverlap(p, item)) {
        item.taken = true;
        if (item.kind === "coin") {
          state.coins += 1;
          state.score += 25;
          burst(item.x + item.w / 2, item.y + item.h / 2, "#f4c84a", 14);
          popup("+25", item.x, item.y);
        } else {
          p.boost = 4.5;
          jump(17);
          burst(item.x + item.w / 2, item.y + item.h / 2, "#39b66a", 16);
          popup("BOTIN!", item.x - 8, item.y, "#39b66a");
        }
        vibrate(18);
      }
    }

    p.boost = Math.max(0, p.boost - dt);

    for (const obstacle of state.obstacles) {
      obstacle.x += obstacle.kind === "rival" ? Math.sin(performance.now() / 580 + obstacle.phase) * .65 : 0;
      if (rectsOverlap({ x: p.x + 8, y: p.y + 8, w: p.w - 16, h: p.h - 12 }, obstacle)) {
        endGame();
        return;
      }
    }

    const desiredCamera = Math.min(state.cameraY, p.y - state.height * .42);
    state.cameraY += (desiredCamera - state.cameraY) * Math.min(1, dt * 5);
    state.highestY = Math.min(state.highestY, p.y);
    state.score = Math.max(state.score, Math.floor(-state.highestY * .18));

    while (state.spawnY > state.cameraY - state.height * 1.25) spawnPlatform();
    const cleanupY = state.cameraY + state.height + 160;
    state.platforms = state.platforms.filter((o) => o.y < cleanupY);
    state.collectibles = state.collectibles.filter((o) => !o.taken && o.y < cleanupY);
    state.obstacles = state.obstacles.filter((o) => o.y < cleanupY);

    updateEffects(dt);
    if (p.y - state.cameraY > state.height + 120) endGame();
    updateHud();
  }

  function updateEffects(dt) {
    state.particles.forEach((part) => {
      part.life -= dt;
      part.x += part.vx * 60 * dt;
      part.y += part.vy * 60 * dt;
      part.vy += 7 * dt;
    });
    state.particles = state.particles.filter((part) => part.life > 0);
    state.popups.forEach((pop) => {
      pop.life -= dt;
      pop.y -= 34 * dt;
    });
    state.popups = state.popups.filter((pop) => pop.life > 0);
  }

  function endGame() {
    state.mode = "over";
    vibrate(45);
    state.best = Math.max(state.best, state.score);
    localStorage.setItem("babyAlboJumpBest", String(state.best));
    finalScoreEl.textContent = state.score;
    finalBestEl.textContent = state.best;
    updateHud();
    overScreen.classList.remove("hidden");
  }

  function draw() {
    ctx.clearRect(0, 0, state.width, state.height);
    drawBackground();
    ctx.save();
    ctx.translate(0, -state.cameraY);
    drawWorld();
    ctx.restore();
    drawEffects();
  }

  function drawBackground() {
    const bg = images.background;
    if (bg?.complete) ctx.drawImage(bg, 0, 0, state.width, state.height);
    ctx.fillStyle = "rgba(0,0,0,.12)";
    ctx.fillRect(0, 0, state.width, state.height);
    ctx.fillStyle = "rgba(255,255,255,.08)";
    for (let y = 80; y < state.height; y += 110) {
      ctx.fillRect(0, y + ((-state.cameraY * .18) % 110), state.width, 1);
    }
  }

  function drawWorld() {
    for (const platform of state.platforms) {
      drawImage(images.platform, platform.x, platform.y, platform.w, platform.h);
      if (platform.type === "moving") {
        ctx.fillStyle = "rgba(255,255,255,.7)";
        ctx.fillRect(platform.x + 18, platform.y + 3, platform.w - 36, 3);
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
      ctx.translate(cx, p.y);
      ctx.scale(p.facing, 1);
      drawImage(images.player, -p.w / 2, 0, p.w, p.h);
      if (p.boost > 0) {
        ctx.globalAlpha = .75;
        ctx.fillStyle = "#39b66a";
        ctx.beginPath();
        ctx.ellipse(0, p.h + 5, 18, 6, 0, 0, Math.PI * 2);
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
      ctx.globalAlpha = Math.max(0, pop.life / .8);
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
  }

  function handleStart(event) {
    if (event) event.preventDefault();
    if (state.mode === "playing") return;
    startGame();
  }

  canvas.addEventListener("touchstart", (event) => {
    if (state.mode !== "playing") return;
    event.preventDefault();
    if (event.touches[0]) setTouch(event.touches[0].clientX);
  }, { passive: false });

  canvas.addEventListener("touchmove", (event) => {
    if (state.mode !== "playing") return;
    event.preventDefault();
    if (event.touches[0]) setTouch(event.touches[0].clientX);
  }, { passive: false });

  canvas.addEventListener("touchend", () => {
    if (state.mode !== "playing") return;
    state.touchX = null;
  });

  canvas.addEventListener("pointerdown", (event) => {
    if (state.mode === "playing") setTouch(event.clientX);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (state.mode === "playing" && (event.pressure || event.buttons)) setTouch(event.clientX);
  });
  canvas.addEventListener("pointerup", () => {
    if (state.mode !== "playing") return;
    state.touchX = null;
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") state.keys.left = true;
    if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") state.keys.right = true;
  });

  window.addEventListener("keyup", (event) => {
    if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") state.keys.left = false;
    if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") state.keys.right = false;
  });

  playButton.addEventListener("click", handleStart);
  playButton.addEventListener("touchend", handleStart, { passive: false });
  retryButton.addEventListener("click", handleStart);
  retryButton.addEventListener("touchend", handleStart, { passive: false });
  shareButton.addEventListener("click", async () => {
    const text = `Mi récord en Baby Albo Jump es ${state.best} puntos. ¿Lo superás?`;
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
