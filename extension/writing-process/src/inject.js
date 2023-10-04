/*
   Inject script. This is a web_accessible_resources used to pass the id 
   of the document as a globally accessible variable to the extension.
   It is called by the injectScript function in writing.js to make the result 
   accessible using an event listener
*/

(function() {
    const result = JSON.stringify(_docs_flag_initialData.info_params.token);
    window.postMessage({ from: 'inject.js', data: result });
})();