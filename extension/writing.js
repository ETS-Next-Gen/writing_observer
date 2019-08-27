/* 
Page script. This is injected into each web page on associated web sites.
*/ 

document.body.style.border = "5px solid blue";

var writing_lasthash = "";
function unique_id() {
    var shaObj = new jsSHA("SHA-256", "TEXT");
    shaObj.update(writing_lasthash);
    shaObj.update(Math.random().toString());
    shaObj.update(Date.now().toString());
    shaObj.update(document.cookie);
    shaObj.update("NaCl");
    shaObj.update(window.location.href);
    writing_lasthash = shaObj.getHash("HEX");
    return writing_lasthash;
}

function doc_id() {
    return googledocs_id_from_url(window.location.href);
}

function this_is_a_google_doc() {
    return window.location.href.search("://docs.google.com/") != -1;
}

function writing_eventlistener(event) {
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = ['altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode', 'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted', 'timeStemp', 'type'];
    for (var property in properties) {
	event_data[properties[property]] = event[properties[property]];
    }
    event_data['date'] = new Date().toLocaleString('en-US');
    event_data['id'] = doc_id();
    console.log(event_data['url']);

    console.log(JSON.stringify(event_data));
    writingjs_ajax(event_data);
}



document.addEventListener("keypress", writing_eventlistener);
document.addEventListener("keydown", writing_eventlistener);
document.addEventListener("keyup", writing_eventlistener);

var iframes = document.getElementsByTagName("iframe")
for(iframe in iframes){
    if(iframes[iframe].contentDocument) {
	iframes[iframe].contentDocument.addEventListener("keypress", writing_eventlistener);
	iframes[iframe].contentDocument.addEventListener("keydown", writing_eventlistener);
	iframes[iframe].contentDocument.addEventListener("keyup", writing_eventlistener);
    }
}


function gmail_text() {
    /*
      This function returns all the editable text in the current gmail
      window. Note that in a threaded discussion, it's possible to
      have several open on the same page.

      This is brittle; Google may change implementation and this will
      break.
     */
    var documents = document.getElementsByClassName("editable");
    for(document in documents) {
	documents[document] = {
	    'text': documents[document].innerHTML
	};
    }
    return documents;
}

function google_docs_title() {
    /*
      Return the title of a Google Docs document
     */
    return document.getElementsByClassName("docs-title-input")[0].value;
}

function google_docs_partial_text() {
    /*
      Return the *loaded* text of a Google Doc. Note that for long
      documents, this may not be the *complete* text since off-screen
      pages may be lazy-loaded. The text omits formatting, which is
      helpful for many types of analysis
     */
    return document.getElementsByClassName("kix-page")[0].innerText;
}

function google_docs_partial_html() {
    /*
      Return the *loaded* HTML of a Google Doc. Note that for long
      documents, this may not be the *complete* HTML, since off-screen
      pages may be lazy-loaded. This includes HTML formatting, which
      may be helpful, but is incredibly messy.
      
      I hate Google's HTML. What's wrong with simple, clean, semantic
      <b> tags? Why do we need something like this instead:
      <span class="kix-wordhtmlgenerator-word-node" style="font-size:14.666666666666666px;font-family:Arial;color:#000000;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;">
      Seriously, Google? 
     */
    return document.getElementsByClassName("kix-page")[0].innerHTML;
}

function executeOnPageSpace(code){
    /* This is from 
       https://stackoverflow.com/questions/9602022/chrome-extension-retrieving-global-variable-from-webpage

       It is used to run code outside of the extension isolation box,
       for example to access page JavaScript variables.
     */
    // create a script tag
    var script = document.createElement('script')
    script.id = 'tmpScript'
    // place the code inside the script. later replace it with execution result.
    script.textContent = 
	'document.getElementById("tmpScript").textContent = JSON.stringify(' + code + ')'
    // attach the script to page
    document.documentElement.appendChild(script)
    // collect execution results
    let result = document.getElementById("tmpScript").textContent
    // remove script from page
    script.remove()
    return JSON.parse(result)
}

function google_docs_version_history() {
    var token = executeOnPageSpace("_docs_flag_initialData.info_params.token");
    metainfo_url = "https://docs.google.com/document/d/"+doc_id()+"/revisions/tiles?id="+doc_id()+"&start=1&showDetailedRevisions=false&filterNamed=false&token="+token+"&includes_info_params=true"
    fetch(metainfo_url).then(function(response) {
	response.text().then(function(text) {
	    tiles = JSON.parse(text.substring(5)); // Google adds a header to prevent JavaScript injection. This removes it.
	    var first_revision = tiles.firstRev;
	    var last_revision = tiles.tileInfo[tiles.tileInfo.length - 1].end;
	    version_history_url = "https://docs.google.com/document/d/"+doc_id()+"/revisions/load?id="+doc_id()+"&start="+first_revision+"&end="+last_revision;
	    console.log(version_history_url);
	    fetch(version_history_url).then(function(history_response) {
		history_response.text().then(function(history_text) {
		    console.log(history_text);
		});
	    });
	});
    });
}

// https://docs.google.com/document/d/1lt_lSfEM9jd7Ga6uzENS_s8ZajcxpE0cKuzXbDoBoyU/revisions/load?id=1lt_lSfEM9jd7Ga6uzENS_s8ZajcxpE0cKuzXbDoBoyU&start=1&end=300

// {"tileInfo":[{"start":1,"end":1,"endMillis":1565618108628,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"DXjr1gUIKJye-Q"},{"start":2,"end":25,"endMillis":1565618606428,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"tzzZJD5qs1k8YQ"},{"start":26,"end":26,"endMillis":1565687165389,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"EFaHxMq5RwIbiA"},{"start":27,"end":131,"endMillis":1565887557347,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"IktkTE-OHb_a4w"},{"start":132,"end":199,"endMillis":1565895985511,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"4-jj6h3QR26WOA"},{"start":200,"end":238,"endMillis":1565906888993,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"u3yYJvJBiVfImg"},{"start":239,"end":243,"endMillis":1566036118386,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"fGom_rH071Lfzg"},{"start":244,"end":248,"endMillis":1566692983735,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"sxMGFwhfT9Akbg"},{"start":249,"end":262,"endMillis":1566748493846,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"Rya8bp1glL8XtQ"},{"start":263,"end":266,"endMillis":1566814345191,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"K7B8GTV1UvSR_g"},{"start":267,"end":268,"endMillis":1566830127167,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"jEfJ5MRCmwhZlg"},{"start":269,"end":301,"endMillis":1566838256185,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"uy2uqc9q0pBQnQ"},{"start":302,"end":302,"endMillis":1566840996445,"users":["10308288613201963581"],"systemRevs":[],"expandable":false,"revisionMac":"pAikpOJ2fomhZg"},{"start":303,"end":307,"endMillis":1566849461292,"users":["10308288613201963581"],"systemRevs":[],"expandable":true,"revisionMac":"OR8lknfQhBqmuQ"}],"userMap":{"10308288613201963581":{"name":"Piotr Mitros","photo":"//lh3.googleusercontent.com/a-/AAuE7mBPq-BL5P1ZZg1N0mh9BPLSSkgBqeN3wnLVH0tZ\u003ds50-c-k-no","defaultPhoto":false,"color":"#26A69A","anonymous":false}},"firstRev":1}

// cookie: S=documents=-0139lI8XPtj5RlM3yMiSMm65NpEPhb1; SID=nAd7sht2a_QMpTbmZR0YK3gCseKEBX_ie8HEMZIDsv9btLkzJuNKN15D4IzbSWAL8eym7Q.; HSID=APez4e6AmTL1EVx2o; SSID=Az1RQ_epFl_39Hmwk; APISID=DY4P1zvmTBZhHgP5/A1yeGjd8U74GTzJ-x; SAPISID=yGBiRuDtlmqqwzs4/AsINvELYvon8jWvGt; ANID=AHWqTUk__nHk8xzlNlnhj60_p6JhVxs6Q7-kDkQvaG82i-nU7_PG1q2K0i96y5S9; SEARCH_SAMESITE=CgQI1o0B; S=explorer=PDpeyuS6wzjoz7SlIiZ9Y6dAiLQ0AGKP; NID=188=ZppA1vlmd9N7uDI7Re0NOBuGAAi9Fgv5CYEMw1y0akPcMuSHTIBmd_MWivVercGRr-ZCOIadtyhK8Rm9ZUzcqwAzJOeXGnALMqpuPamh0lQguPPZjjldOckFCaPSrICJUCZ4zW31hAyGNBtPMFe-SYe6UdIBN_k5DlsprTZDUc_fmFpMbgEwlGG_kIKyonhpWX4OdkaUYPLJJCYqCNrJSEA3YpLkTFyY5ArVd2HthIyd7UpshgxAYw1lqh_XHIEe1Kb4v2rSeS9IuOl70CoOqydi69b6N5bjoGc2qi_QZeFmSLp-RU72XYpcGVB5dNVC-mvUsNzfRQaUyaonl7I44_R6Off6aZ3TwiOe5ZnPxw2BiqdPqsE3CgeZi4ZdSw3JXXPliNMlvt9IIwuQ7aDzaGbLH-CFueO6g8B92JDGcJ0P; 1P_JAR=2019-8-26-19; SIDCC=AN0-TYvNZxiSjuj5_gFXAjiyFnr1RDCQjEedbdU0SHElyA1F12Cek9tYKjiDrDJhOdX7YvQb_lfPVg; GFE_RTT=71

// }


function writing_onload() {
    if(this_is_a_google_doc()) {
	writingjs_ajax({
	    "event_type": "Google Docs loaded",
	    "partial_text": google_docs_partial_text(),
	    //    "partial_html": google_docs_partial_html(),
	    "title": google_docs_title(),
	    "id": doc_id
	})
	google_docs_version_history();
    }
}

window.addEventListener("load", writing_onload);

console.log(unique_id());
