//
// This is preload Learning Observer libraries.
//
// Most of this is for path management.
//

function lo_modulepath(rel_path) {
    // This is used to retrieve URLs of relative
    // files in the same git repo.
    const path = new URL(document.URL).pathname;
    const last_slash = path.lastIndexOf("/");
    const base_path = path.slice(0, last_slash+1);
    return base_path + rel_path;
}

function lo_thirdpartypath(rel_path) {
    // This is used to retrieve URLs of external libraries
    return "/static/3rd_party/"+rel_path;
}

function requiremodulelib(lib) {
    return lo_modulepath(lib);
}

function requireexternallib(lib) {
    return lo_thirdpartypath(lib)
}

function requiremoduletext(text) {
    return "/static/3rd_party/text.js!"+lo_modulepath(text);
}

function requiresystemtext(text) {
    return "/static/3rd_party/text.js!/static/"+text
}

function requireconfig() {
    return "/static/3rd_party/text.js!/config.json";
}
