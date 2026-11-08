/* Проверка доступа к курсу. Пароли хранятся только в виде хешей. */
(function () {
  "use strict";

  var USERS = Array.isArray(window.COURSE_USERS) ? window.COURSE_USERS : [];
  var AUTH_KEY = "aiEduAuth.v1";
  var LOCK_KEY = "aiEduAuth.lock.v1";
  var MAX_ATTEMPTS = 5;
  var LOCK_MS = 30000;

  function rotr(x, n) {
    return ((x >>> n) | (x << (32 - n))) >>> 0;
  }

  function sha256Bytes(bytes) {
    var K = [
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ];
    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var l = bytes.length;
    var total = ((l + 9 + 63) >> 6) << 6;
    var msg = new Uint8Array(total);
    msg.set(bytes);
    msg[l] = 0x80;
    var bitLen = l * 8;
    var view = new DataView(msg.buffer);
    view.setUint32(total - 8, Math.floor(bitLen / 0x100000000));
    view.setUint32(total - 4, bitLen >>> 0);
    var w = new Uint32Array(64);

    for (var off = 0; off < total; off += 64) {
      for (var i = 0; i < 16; i++) w[i] = view.getUint32(off + i * 4);
      for (var i2 = 16; i2 < 64; i2++) {
        var s0 = rotr(w[i2 - 15], 7) ^ rotr(w[i2 - 15], 18) ^ (w[i2 - 15] >>> 3);
        var s1 = rotr(w[i2 - 2], 17) ^ rotr(w[i2 - 2], 19) ^ (w[i2 - 2] >>> 10);
        w[i2] = (w[i2 - 16] + s0 + w[i2 - 7] + s1) >>> 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (var j = 0; j < 64; j++) {
        var S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (h + S1 + ch + K[j] + w[j]) >>> 0;
        var S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0;
        d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0;
      H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0;
      H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }

    var out = new Uint8Array(32);
    var ov = new DataView(out.buffer);
    for (var k = 0; k < 8; k++) ov.setUint32(k * 4, H[k]);
    return out;
  }

  function hexToBytes(hex) {
    var out = new Uint8Array(hex.length / 2);
    for (var i = 0; i < out.length; i++) out[i] = parseInt(hex.substr(i * 2, 2), 16);
    return out;
  }

  function bytesToHex(bytes) {
    var s = "";
    for (var i = 0; i < bytes.length; i++) s += ("0" + bytes[i].toString(16)).slice(-2);
    return s;
  }

  function hashPassword(password, saltHex, iterations) {
    var enc = new TextEncoder();
    var salt = hexToBytes(saltHex);
    var h = sha256Bytes(enc.encode(saltHex + ":" + password));
    for (var i = 1; i < iterations; i++) {
      var buf = new Uint8Array(h.length + salt.length);
      buf.set(h, 0);
      buf.set(salt, h.length);
      h = sha256Bytes(buf);
    }
    return bytesToHex(h);
  }

  function normalize(login) {
    return String(login == null ? "" : login).trim().toLowerCase();
  }

  function findUser(login) {
    var key = normalize(login);
    for (var i = 0; i < USERS.length; i++) {
      if (USERS[i].l === key) return USERS[i];
    }
    return null;
  }

  function verify(login, password) {
    var user = findUser(login);
    if (!user || typeof password !== "string" || !password) return false;
    try {
      return hashPassword(password, user.s, user.i) === user.h;
    } catch (e) {
      return false;
    }
  }

  function readStore(storeKey, store) {
    try {
      var raw = store.getItem(storeKey);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || !data.login || !findUser(data.login)) return null;
      return data;
    } catch (e) {
      return null;
    }
  }

  function current() {
    try {
      var data = readStore(AUTH_KEY, window.localStorage);
      if (data) return { login: data.login, remember: true };
      data = readStore(AUTH_KEY, window.sessionStorage);
      if (data) return { login: data.login, remember: false };
    } catch (e) {}
    return null;
  }

  function lockInfo() {
    try {
      var raw = window.localStorage.getItem(LOCK_KEY);
      if (!raw) return { attempts: 0, until: 0 };
      var data = JSON.parse(raw);
      if (!data || typeof data.until !== "number") return { attempts: 0, until: 0 };
      return { attempts: Number(data.attempts) || 0, until: data.until };
    } catch (e) {
      return { attempts: 0, until: 0 };
    }
  }

  function writeLock(data) {
    try { window.localStorage.setItem(LOCK_KEY, JSON.stringify(data)); } catch (e) {}
  }

  function recordFailure() {
    var info = lockInfo();
    var attempts = info.attempts + 1;
    var until = attempts >= MAX_ATTEMPTS ? Date.now() + LOCK_MS : 0;
    writeLock({ attempts: until ? 0 : attempts, until: until });
    return { attempts: attempts, until: until };
  }

  function clearFailures() {
    try { window.localStorage.removeItem(LOCK_KEY); } catch (e) {}
  }

  function login(loginValue, password, remember) {
    var loginName = normalize(loginValue);
    if (!loginName || !password) return { ok: false, reason: "empty" };
    var lock = lockInfo();
    if (lock.until && lock.until > Date.now()) {
      return { ok: false, reason: "locked", wait: Math.ceil((lock.until - Date.now()) / 1000) };
    }
    if (!verify(loginName, password)) {
      var fail = recordFailure();
      if (fail.until) return { ok: false, reason: "locked", wait: Math.ceil(LOCK_MS / 1000) };
      return { ok: false, reason: "invalid", left: Math.max(0, MAX_ATTEMPTS - fail.attempts) };
    }
    clearFailures();
    var payload = JSON.stringify({ login: loginName, ts: Date.now() });
    try {
      if (remember) {
        window.localStorage.setItem(AUTH_KEY, payload);
        try { window.sessionStorage.removeItem(AUTH_KEY); } catch (e2) {}
      } else {
        window.sessionStorage.setItem(AUTH_KEY, payload);
        try { window.localStorage.removeItem(AUTH_KEY); } catch (e3) {}
      }
    } catch (e4) {
      return { ok: false, reason: "storage" };
    }
    return { ok: true, login: loginName };
  }

  function logout() {
    try { window.localStorage.removeItem(AUTH_KEY); } catch (e) {}
    try { window.sessionStorage.removeItem(AUTH_KEY); } catch (e) {}
  }

  window.COURSE_AUTH = {
    current: current,
    login: login,
    logout: logout,
    verify: verify,
    normalize: normalize,
    _hashPassword: hashPassword
  };
})();
