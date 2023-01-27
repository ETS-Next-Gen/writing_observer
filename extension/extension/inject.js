let script = document.createElement('script')
script.id = 'tmpScript'

const code = "_docs_flag_initialData.info_params.token"
script.textContent = 'document.getElementById("tmpScript").textContent = JSON.stringify(' + code + ')'

document.documentElement.appendChild(script)

let result = script.textContent

window.postMessage({ from: 'inject.js', data: result })

script.remove()