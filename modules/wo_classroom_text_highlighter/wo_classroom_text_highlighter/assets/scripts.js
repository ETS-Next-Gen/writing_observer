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

// TODO this ought to move to a more common place
async function hashObject (obj) {
  const jsonString = JSON.stringify(obj);
  const encoder = new TextEncoder();
  const data = encoder.encode(jsonString);

  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');

  return hashHex;
}

// TODO some of this will move to the communication protocol, but for now
// it lives here
function formatStudentData (student, selectedHighlights) {
  // TODO make sure the comm protocol is providing the doc id
  const highlightBreakpoints = selectedHighlights.reduce((acc, option) => {
    const offsets = student[option.id]?.offsets || [];
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
  return {
    profile: student.profile,
    availableDocuments: [{ id: 'latest', title: 'Latest' }],
    documents: {
      latest: {
        text: student.text,
        breakpoints: highlightBreakpoints,
        optionHash: ''
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

      // TODO pass this to the communication protocol
      const optionsHash = hashObject(fullOptions);

      const nlpOptions = determineSelectedNLPOptionsList(fullOptions);
      decodedParams.nlp_options = nlpOptions;
      const outgoingMessage = {
        wo_classroom_text_highlighter_query: {
          execution_dag: 'writing_observer',
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
  populateOutput: function (wsStorageData, options, width, height, showHeader) {
    console.log('wsStorageData', wsStorageData);
    if (!wsStorageData) {
      return 'No students';
    }
    const data = wsStorageData?.wo_classroom_text_highlighter_query?.nlp_combined ?? [];
    // Check if the returned items have errors
    if (typeof data === 'object' && !Array.isArray(data) && data !== null && 'error' in data) {
      return window.dash_clientside.no_update;
    }
    let output = [];
    // TODO now for the fun stuff. We need to take the options, determine which ones we want
    // and pass those to the apppropriate place.
    // how should student look here?

    const selectedHighlights = options.filter(option => option.types?.highlight?.value);
    // TODO do something with the selected metrics/progress bars/etc.
    const selectedMetrics = options.filter(option => option.types?.metric?.value);

    for (const student of data) {
      const studentTile = createDashComponent(
        LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
        {
          showHeader,
          style: { width: `${100 / width}%`, height: `${height}px` },
          studentInfo: formatStudentData(student, selectedHighlights),
          selectedDocument: 'latest',
          childComponent: createDashComponent(LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText', {}),
          id: { type: 'WOStudentTextTile', index: student.user_id }
        }
      );
      output = output.concat(studentTile);
    }
    return output;
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
