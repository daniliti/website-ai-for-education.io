/* SCORM 1.2 — необязательная интеграция. Если API нет, курс работает автономно. */
(function () {
  var api = null;
  var initialized = false;
  var finished = false;

  function findAPI(win) {
    var tries = 0;
    while (win && !win.API && win.parent && win.parent !== win && tries < 500) {
      win = win.parent;
      tries++;
    }
    return (win && win.API) ? win.API : null;
  }

  function init() {
    if (initialized) return true;
    if (!api) api = findAPI(window);
    if (!api) return false;
    try {
      if (api.LMSInitialize("")) {
        initialized = true;
        var status = api.LMSGetValue("cmi.core.lesson_status");
        if (!status || status === "not attempted") {
          api.LMSSetValue("cmi.core.lesson_status", "incomplete");
        }
        api.LMSCommit("");
        return true;
      }
    } catch (e) {}
    return false;
  }

  function setValue(key, value) {
    if (!init()) return;
    try {
      api.LMSSetValue(key, String(value));
      api.LMSCommit("");
    } catch (e) {}
  }

  function setCompleted(done) {
    setValue("cmi.core.lesson_status", done ? "completed" : "incomplete");
  }

  function setScore(raw, max) {
    setValue("cmi.core.score.raw", raw);
    setValue("cmi.core.score.max", max || 16);
    setValue("cmi.core.score.min", 0);
  }

  function setLocation(location) {
    setValue("cmi.core.lesson_location", location || "");
  }

  function getLocation() {
    if (!init()) return "";
    try { return api.LMSGetValue("cmi.core.lesson_location") || ""; } catch (e) { return ""; }
  }

  function finish() {
    if (!initialized || finished) return;
    try { api.LMSCommit(""); api.LMSFinish(""); finished = true; } catch (e) {}
  }

  window.SCORM = {
    init: init,
    setCompleted: setCompleted,
    setScore: setScore,
    setLocation: setLocation,
    getLocation: getLocation,
    finish: finish
  };

  window.addEventListener("load", init);
  window.addEventListener("beforeunload", finish);
  window.addEventListener("pagehide", finish);
})();
