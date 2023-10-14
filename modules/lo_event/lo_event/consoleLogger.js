function consoleLog(event) {
  console.log(event);
  this.init = function() { console.log("Initializing console logger!") };
  this.preauth = function(metadata) { console.log("Preauth:", preauth) };
  this.postauth = function(metadata) { console.log("Postauth:", postauth) };
  this.lo_name="Console Logger";
}

export function consoleLogger () {
  /*
  Log to browser JavaScript console
  */
  return consoleLog;
}
