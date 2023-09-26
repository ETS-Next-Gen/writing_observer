const activityType_api = require("./xapi/activityType.json");
const attachmentUsage_api = require("./xapi/attachmentUsage.json");
const extension_api = require("./xapi/extension.json");
const profile_api = require("./xapi/profile.json");
const verb_api = require("./xapi/verb.json");

function aaev_selector(t) {
    const name_field = t.metadata.metadata.name;
    return name_field['en-US'] || name_field['en-us'];
}

function clean_name(n) {
    return n.toUpperCase().trim().replace(/ |-|\./g, '_').replace(/[()]/g, '');
}

function to_dicts(json_block, selector, namesDict, objectsDict) {
    for (let i = 0; i < json_block.length; i++) {
        const name = clean_name(selector(json_block[i]))
        namesDict[name] = name;
        objectsDict[name] = json_block[i];
      }      
}

const ACTIVITYTYPE = {};
const ActivityTypeObjects = {};
to_dicts(activityType_api, aaev_selector, ACTIVITYTYPE, ActivityTypeObjects);

const ATTACHMENTUSAGE = {};
const AttachmentUsageObjects = {};
to_dicts(attachmentUsage_api, aaev_selector, ATTACHMENTUSAGE, AttachmentUsageObjects);

const EXTENSION = {};
const ExtensionObjects = {};
to_dicts(extension_api, aaev_selector, EXTENSION, ExtensionObjects);

const PROFILE = {};
const ProfileObjects = {};
to_dicts(profile_api, (t) => t.name, PROFILE, ProfileObjects);

const VERB = {};
const VerbObjects = {};
to_dicts(verb_api, aaev_selector, VERB, VerbObjects);

module.exports = {
    ACTIVITYTYPE, ActivityTypeObjects,
    ATTACHMENTUSAGE, AttachmentUsageObjects,
    EXTENSION, ExtensionObjects,
    PROFILE, ProfileObjects,
    VERB, VerbObjects
};
