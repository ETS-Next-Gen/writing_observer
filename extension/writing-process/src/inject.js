/*
   Inject script. This is a web_accessible_resources used to pass the id 
   of the document as a globally accessible variable to the extension.
   It is called by the injectScript function in writing.js to make the result 
   accessible using an event listener.

   TODO:
   * We don't really understand this code. It should be commented
   * In particular, why are we using an IIFE (immediately invoked function
     expression) rather than just the code?

     If this is a relic, it should be cleaned up. If this has a
     reason, it should be documented.
*/

(function() {
    const result = JSON.stringify(_docs_flag_initialData.info_params.token);
    window.postMessage({ from: 'inject.js', data: result });
})();
