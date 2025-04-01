/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

// Initialize the `dash_clientside` object if it doesn't exist
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

const DASH_HTML_COMPONENTS = 'dash_html_components';
const DASH_CORE_COMPONENTS = 'dash_core_components';
const DASH_BOOTSTRAP_COMPONENTS = 'dash_bootstrap_components';
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
function formatStudentData (student, selectedHighlights) {
  let profile = {};
  const documents = {};
  for (const document in student.documents || []) {
    const breakpoints = selectedHighlights.reduce((acc, option) => {
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
    const text = student.documents[document].text;
    const optionHash = student.documents[document].option_hash;
    profile = student.documents[document].profile;
    documents[document] = { text, optionHash, breakpoints };
  }
  let availableDocuments = [];
  if ('availableDocuments' in student) {
    availableDocuments = Object.keys(student.availableDocuments).map(id => ({
      id,
      title: student.availableDocuments[id].title || id,
      last_access: student.availableDocuments[id].last_access || null
    }));
  }
  return {
    profile,
    availableDocuments,
    documents
  };
}

function styleStudentTile (width, height) {
  return { width: `${(100 - width) / width}%`, height: `${height}px` };
}

window.dash_clientside.wo_classroom_text_highlighter = {
  /**
   * Send updated queries to the communication protocol.
   * @param {object} wsReadyState LOConnection status object
   * @param {string} urlHash query string from hash for determining course id
   * @returns stringified json object that is sent to the communication protocl
   */
  sendToLOConnection: async function (wsReadyState, urlHash, docKwargs, fullOptions) {
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
      decodedParams.doc_source = docKwargs.src;
      decodedParams.doc_source_kwargs = docKwargs.kwargs;
      const outgoingMessage = {
        wo_classroom_text_highlighter_query: {
          execution_dag: 'writing_observer',
          target_exports: ['docs_with_nlp_annotations', 'document_sources', 'document_list'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  // toggleOptions: function (clicks, isOpen) {
  //   if (!clicks) {
  //     return window.dash_clientside.no_update;
  //   }
  //   return !isOpen;
  // },

  toggleOptions: function (clicks, shown) {
    if (!clicks) {
      return window.dash_clientside.no_update;
    }
    const optionPrefix = 'wo-classroom-text-highlighter-options';
    if (shown.includes(optionPrefix)) {
      shown = shown.filter(item => item !== optionPrefix);
    } else {
      shown = shown.concat(optionPrefix);
    }
    return shown;
  },

  closeOptions: function (clicks, shown) {
    if (!clicks) { return window.dash_clientside.no_update; }
    shown = shown.filter(item => item !== 'wo-classroom-text-highlighter-options');
    return shown;
  },

  adjustTileSize: function (width, height, studentIds) {
    const total = studentIds.length;
    return Array(total).fill(styleStudentTile(width, height));
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
    // console.log('wsStorageData', wsStorageData);
    if (!wsStorageData?.students) {
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
    const students = wsStorageData.students;
    for (const student in students) {
      const selectedDocument = students[student].doc_id || Object.keys(students[student].documents || {})[0] || '';
      const studentTile = createDashComponent(
        LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
        {
          showHeader,
          studentInfo: formatStudentData(students[student], selectedHighlights),
          // TODO the selectedDocument ought to remain the same upon updating the student object
          // i.e. it should be pulled from the current client student state
          selectedDocument,
          childComponent: createDashComponent(LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText', {}),
          id: { type: 'WOStudentTextTile', index: student },
          currentOptionHash: optionHash,
          className: 'h-100'
        }
      );
      const tileWrapper = createDashComponent(
        DASH_HTML_COMPONENTS, 'Div',
        {
          className: 'position-relative mb-2',
          children: [
            studentTile,
            createDashComponent(
              DASH_BOOTSTRAP_COMPONENTS, 'Button',
              {
                id: { type: 'WOStudentTileExpand', index: student },
                children: createDashComponent(DASH_HTML_COMPONENTS, 'I', { className: 'fas fa-expand' }),
                class_name: 'position-absolute top-0 end-0 m-1',
                color: 'transparent'
              }
            )
          ],
          id: { type: 'WOStudentTile', index: student },
          style: styleStudentTile(width, height)
        }
      );
      output = output.concat(tileWrapper);
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
  },

  updateLoadingInformation: async function (wsStorageData, nlpOptions) {
    const noLoading = [false, 0, ''];
    if (!wsStorageData?.students) {
      return noLoading;
    }
    const students = wsStorageData.students;
    const promptHash = await hashObject(nlpOptions);
    const returnedResponses = Object.values(students).filter(student => checkForResponse(student, promptHash)).length;
    const totalStudents = Object.keys(students).length;
    if (totalStudents === returnedResponses) { return noLoading; }
    const loadingProgress = returnedResponses / totalStudents + 0.1;
    const outputText = `Fetching responses from server. This will take a few minutes. (${returnedResponses}/${totalStudents} received)`;
    return [true, loadingProgress, outputText];
  },

  expandCurrentStudent: function (clicks, children, ids, shownPanels, currentChild) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }
    let child = '';
    let id = null;
    if (triggeredItem?.type === 'WOStudentTile') {
      if (!currentChild) { return window.dash_clientside.no_update; }
      id = currentChild?.props.id.index;
    } else if (triggeredItem?.type === 'WOStudentTileExpand') {
      id = triggeredItem?.index;
      shownPanels = shownPanels.concat('wo-classroom-text-highlighter-expanded-student-panel');
    } else {
      return window.dash_clientside.no_update;
    }
    const index = ids.findIndex(item => item.index === id);
    child = children[index][0];
    return [child, shownPanels];
  },

  closeExpandedStudent: function (clicks, shown) {
    if (!clicks) { return window.dash_clientside.no_update; }
    shown = shown.filter(item => item !== 'wo-classroom-text-highlighter-expanded-student-panel');
    return shown;
  },

  updateLegend: function (options) {
    const selectedHighlights = options.filter(option => option.types?.highlight?.value);
    if (selectedHighlights.length === 0) {
      return ['No options selected. Click on the `Highlight Options` to select them.', 0];
    }
    let output = selectedHighlights.map(highlight => {
      const color = highlight.types.highlight.color;
      const legendItem = createDashComponent(
        DASH_HTML_COMPONENTS, 'Div',
        {
          children: [
            createDashComponent(
              DASH_HTML_COMPONENTS, 'Span',
              { style: { width: '0.875rem', height: '0.875rem', backgroundColor: color, display: 'inline-block', marginRight: '0.5rem' } }
            ),
            highlight.label
          ]
        }
      );
      return legendItem;
    });
    output = output.concat('Note: words in the student text may have multiple highlights. Hover over a word for the full list of which options apply');
    return [output, selectedHighlights.length];
  }
};
