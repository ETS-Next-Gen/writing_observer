/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

// Initialize the `dash_clientside` object if it doesn't exist
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

const DASH_HTML_COMPONENTS = 'dash_html_components';
const LO_DASH_REACT_COMPONENTS = 'lo_dash_react_components';

// TODO this ought to move to a more common place
function createDashComponent (namespace, type, props) {
  return { namespace, type, props };
}

function determineSelectedNLPOptionsList (options) {
  return options.filter(option =>
    (option.types?.highlight?.value === true) ||
    (option.types?.metric?.value === true)
  ).map(option => option.id);
}

// TODO this ought to move to a more common place like liblo.js
async function hashObject (obj) {
  const jsonString = JSON.stringify(obj);
  const encoder = new TextEncoder();
  const data = encoder.encode(jsonString);

  // Check if crypto.subtle is available
  if (crypto && crypto.subtle) {
    try {
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
      return hashHex;
    } catch (error) {
      console.warn('crypto.subtle.digest failed; falling back to simple hash.');
    }
  }

  // Fallback to the simple hash if crypto.subtle is unavailable
  return simpleHash(jsonString);
}

function simpleHash (str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0; // Convert to 32-bit integer
  }
  return hash.toString(16);
}

// TODO some of this will move to the communication protocol, but for now
// it lives here
// Currently the system only handles grabbing the first document available
// from the student and populates it under latest. We shouldn't hardcode
// anything like latest here and instead pull it from the communication protocol
function formatStudentData (student, selectedHighlights) {
  // TODO this ought to come from the comm protocol
  const document = Object.keys(student.documents)[0];

  // TODO make sure the comm protocol is providing the doc id
  const highlightBreakpoints = selectedHighlights.reduce((acc, option) => {
    const offsets = student.documents[document][option.id]?.offsets || [];
    if (offsets) {
      const modifiedOffsets = offsets.map(offset => {
        return {
          id: '',
          tooltip: option.label,
          start: offset[0],
          offset: offset[1],
          style: { backgroundColor: option.types.highlight.color }
        };
      });
      acc = acc.concat(modifiedOffsets);
    }
    return acc;
  }, []);
  // const availableDocuments = Object.keys(student.docs).map(id => ({
  //   id,
  //   title: student.docs[id].title || id
  // }));
  // availableDocuments.push({ id: 'latest', title: 'Latest' });
  const availableDocuments = [{ id: 'latest', title: 'Latest' }]
  // TODO currently we only populate the latest data of the student documents
  // this is currently the muddiest part of the data flow and ought to be
  // cleaned up.
  return {
    profile: student.documents[document].profile,
    availableDocuments,
    documents: {
      latest: {
        text: student.documents[document].text,
        breakpoints: highlightBreakpoints,
        optionHash: student.documents[document].option_hash
      }
    }
  };
}

window.dash_clientside.wo_classroom_text_highlighter = {
  /**
   * Send updated queries to the communication protocol.
   * @param {object} wsReadyState LOConnection status object
   * @param {string} urlHash query string from hash for determining course id
   * @returns stringified json object that is sent to the communication protocl
   */
  sendToLOConnection: async function (wsReadyState, urlHash, fullOptions) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update;
    }
    if (wsReadyState.readyState === 1) {
      if (urlHash.length === 0) { return window.dash_clientside.no_update; }
      const decodedParams = decode_string_dict(urlHash.slice(1));
      if (!decodedParams.course_id) { return window.dash_clientside.no_update; }

      const optionsHash = await hashObject(fullOptions);
      const nlpOptions = determineSelectedNLPOptionsList(fullOptions);
      decodedParams.nlp_options = nlpOptions;
      decodedParams.option_hash = optionsHash;
      const outgoingMessage = {
        wo_classroom_text_highlighter_query: {
          execution_dag: 'writing_observer',
          // TODO add `doc_list` here when available
          target_exports: ['docs_with_nlp_annotations'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  toggleOptions: function (clicks, isOpen) {
    if (!clicks) {
      return window.dash_clientside.no_update;
    }
    return !isOpen;
  },

  adjustTileSize: function (width, height, studentIds) {
    const total = studentIds.length;
    return Array(total).fill({ width: `${100 / width}%`, height: `${height}px` });
  },

  showHideHeader: function (show, ids) {
    const total = ids.length;
    return Array(total).fill(show ? 'd-none' : '');
  },

  updateCurrentOptionHash: async function (options, ids) {
    const optionHash = await hashObject(options);
    const total = ids.length;
    return Array(total).fill(optionHash);
  },

  /**
   * Build the student UI components based on the stored websocket data
   * @param {*} wsStorageData information stored in the websocket store
   * @returns Dash object to be displayed on page
   */
  populateOutput: async function (wsStorageData, options, width, height, showHeader) {
    console.log('wsStorageData', wsStorageData);
    if (!wsStorageData) {
      return 'No students';
    }
    let output = [];

    const selectedHighlights = options.filter(option => option.types?.highlight?.value);
    // TODO do something with the selected metrics/progress bars/etc.
    // currently due to a HACK with how we pass data to the `childComponent`
    // we are only able to have a single child and we expect it to be the
    // `WOAnnotatedText` component.
    const selectedMetrics = options.filter(option => option.types?.metric?.value);

    const optionHash = await hashObject(options);

    for (const student in wsStorageData) {
      const studentTile = createDashComponent(
        LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
        {
          showHeader,
          style: { width: `${100 / width}%`, height: `${height}px` },
          studentInfo: formatStudentData(wsStorageData[student], selectedHighlights),
          // TODO the selectedDocument ought to remain the same upon updating the student object
          // i.e. it should be pulled from the current client student state
          selectedDocument: 'latest',
          childComponent: createDashComponent(LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText', {}),
          id: { type: 'WOStudentTextTile', index: student },
          currentOptionHash: optionHash
        }
      );
      output = output.concat(studentTile);
    }
    return output;
  },

  updateAlertWithError: function (error) {
    if (Object.keys(error).length === 0) {
      return ['', false, ''];
    }
    const text = 'Oops! Something went wrong ' +
                 "on our end. We've noted the " +
                 'issue. Please try again later, or consider ' +
                 'exploring a different dashboard for now. ' +
                 'Thanks for your patience!';
    return [text, true, error];
  },

  addPreset: function (clicks, name, options, store) {
    if (!clicks) { return store; }
    const copy = { ...store };
    copy[name] = options;
    return copy;
  },

  applyPreset: function (clicks, data) {
    const preset = window.dash_clientside.callback_context?.triggered_id.index ?? null;
    const itemsClicked = clicks.some(item => item !== undefined);
    if (!preset | !itemsClicked) { return window.dash_clientside.no_update; }
    return data[preset];
  }
};
