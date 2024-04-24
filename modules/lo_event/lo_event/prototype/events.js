let events = {
  abort: {properties: [], functions: {}},
  afterprint: {properties: [], functions: {}},
  animationend: {properties: [], functions: {}},
  animationiteration: {properties: [], functions: {}},
  animationstart: {properties: [], functions: {}},
  beforeprint: {properties: [], functions: {}},
  beforeunload: {properties: [], functions: {}},
  blur: {properties: [], functions: {}},
  canplay: {properties: [], functions: {}},
  canplaythrough: {properties: [], functions: {}},
  change: {properties: [], functions: {}},
  click: {properties: [], functions: {}},
  contextmenu: {properties: [], functions: {}},
  copy: {properties: [], functions: {}},
  cut: {properties: [], functions: {}},
  dblclick: {properties: [], functions: {}},
//  drag: {properties: [], functions: {}}, <-- Large number of events
  dragend: {properties: [], functions: {}},
  dragenter: {properties: [], functions: {}},
  dragleave: {properties: [], functions: {}},
//  dragover: {properties: [], functions: {}},
  dragstart: {properties: [], functions: {}},
  drop: {properties: [], functions: {}},
  durationchange: {properties: [], functions: {}},
  ended: {properties: [], functions: {}},
  error: {properties: [], functions: {}},
  focus: {properties: [], functions: {}},
  focusin: {properties: [], functions: {}},
  focusout: {properties: [], functions: {}},
  fullscreenchange: {properties: [], functions: {}},
  fullscreenerror: {properties: [], functions: {}},
  hashchange: {properties: [], functions: {}},
  input: {properties: [], functions: {}},
  invalid: {properties: [], functions: {}},
  keydown: {properties: [], functions: {}},
  keypress: {properties: [], functions: {}},
  keyup: {properties: [], functions: {}},
  load: {properties: [], functions: {}},
  loadeddata: {properties: [], functions: {}},
  loadedmetadata: {properties: [], functions: {}},
  loadstart: {properties: [], functions: {}},
//  message: {properties: [], functions: {}}, <-- We want to avoid the possibility of infinite loops
  mousedown: {properties: [], functions: {}},
  mouseenter: {properties: [], functions: {}},
  mouseleave: {properties: [], functions: {}},
//  mousemove: {properties: [], functions: {}}, <-- Massive number of events
//  mouseover: {properties: [], functions: {}}, <-- Moderate number of events
//  mouseout: {properties: [], functions: {}}, <-- Moderate number of events
  mouseup: {properties: [], functions: {}},
  offline: {properties: [], functions: {}},
  online: {properties: [], functions: {}},
//  open: {properties: [], functions: {}}, <-- We want to avoid the possibility of infinite loops
  pagehide: {properties: [], functions: {}},
  pageshow: {properties: [], functions: {}},
  paste: {properties: [], functions: {}},
  pause: {properties: [], functions: {}},
  play: {properties: [], functions: {}},
  playing: {properties: [], functions: {}},
  progress: {properties: [], functions: {}},
  ratechange: {properties: [], functions: {}},
//  resize: {properties: [], functions: {}},  <-- This would be helpful with a debounce, so we have the final resize
  reset: {properties: [], functions: {}},
//  scroll: {properties: [], functions: {}},  <-- This would be helpful with a debounce, so we have the final resize
  search: {properties: [], functions: {}},
  seeked: {properties: [], functions: {}},
//  seeking: {properties: [], functions: {}}, <-- Many events
  select: {properties: [], functions: {}},
  show: {properties: [], functions: {}},
  stalled: {properties: [], functions: {}},
  submit: {properties: [], functions: {}},
  suspend: {properties: [], functions: {}},
//  timeupdate: {properties: [], functions: {}}, <-- Many events
  toggle: {properties: [], functions: {}},
  touchcancel: {properties: [], functions: {}},
  touchend: {properties: [], functions: {}},
//  touchmove: {properties: [], functions: {}}, <- Many events
  touchstart: {properties: [], functions: {}},
  transitionend: {properties: [], functions: {}},
  unload: {properties: [], functions: {}},
  volumechange: {properties: [], functions: {}},
  waiting: {properties: [], functions: {}},
  wheel: {properties: [], functions: {}}
}

function logToDiv(text) {
  // Select the output div
  var outputDiv = document.getElementById("output");

  // Append the text to the div
  outputDiv.innerHTML += text + "<br>";
  console.log(text);
}

function eventListner(event) {
  logToDiv(event);
}

for (let key in events) {
  document.addEventListener(key, eventListner);
}
