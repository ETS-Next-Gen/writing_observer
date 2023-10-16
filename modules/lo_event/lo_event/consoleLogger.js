function consoleLog(event) {
  console.log(event);
}

export function consoleLogger () {
  /*
  Log to browser JavaScript console
  */
  consoleLog.init = function() { console.log("Initializing console logger!") };
  consoleLog.preauth = function(metadata) { console.log("Preauth:", metadata) };
  consoleLog.postauth = function(metadata) { console.log("Postauth:", metadata) };
  consoleLog.setField = function(metadata) { console.log("setField:", metadata) };
  consoleLog.lo_name="Console Logger";

  return consoleLog;
}
