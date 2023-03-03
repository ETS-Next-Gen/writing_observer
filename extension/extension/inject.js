/*
   Inject script. This is a web_accessible_resources used to pass the id 
   of the document as a globally accessible variable to the extension.
   It is called by the injectScript function in writing.js to make the result 
   accessible using an event listener
*/

let script = document.createElement('script')
script.id = 'tmpScript'

const code = "_docs_flag_initialData.info_params.token"
script.textContent = `document.getElementById("tmpScript").textContent = JSON.stringify(${code})`

document.documentElement.appendChild(script)

let result = script.textContent

window.postMessage({ from: 'inject.js', data: result })

script.remove()
