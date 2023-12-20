/**
 * General scripts used for the bulk essay analysis dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {}
}

pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/3rd_party/pdf.worker.min.js'

const createStudentCard = function (student, prompt) {
  const header = {
    namespace: 'dash_bootstrap_components',
    type: 'CardHeader',
    props: { children: student.profile.name.full_name }
  }
  const studentText = {
    namespace: 'lo_dash_react_components',
    type: 'WOAnnotatedText',
    props: { text: student.text, breakpoints: [], className: 'border-end' }
  }
  const feedbackMessage = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: student?.feedback ? student.feedback : '',
      className: student?.feedback ? 'p-1 overflow-auto' : '',
      style: { whiteSpace: 'pre-line' }
    }
  }
  const feedbackLoading = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: {
        namespace: 'dash_bootstrap_components',
        type: 'Spinner',
        props: {}
      },
      className: 'text-center'
    }
  }
  const feedback = prompt === student.prompt ? feedbackMessage : feedbackLoading
  const body = {
    namespace: 'lo_dash_react_components',
    type: 'LOPanelLayout',
    props: {
      children: studentText,
      panels: [{ children: feedback, id: 'feedback-text', width: '40%' }],
      shown: ['feedback-text'],
      className: 'overflow-auto p-1'
    }
  }
  const card = {
    namespace: 'dash_bootstrap_components',
    type: 'Card',
    props: {
      children: [header, body],
      style: { maxHeight: '375px' }
    }
  }
  return {
    namespace: 'dash_bootstrap_components',
    type: 'Col',
    props: {
      children: card,
      id: student.user_id,
      width: 4
    }
  }
}

const charactersAfterChar = function (str, char) {
  const commaIndex = str.indexOf(char)
  if (commaIndex === -1) {
    return ''
  }
  return str.slice(commaIndex + 1).trim()
}

const extractPDF = async function (base64String) {
  const pdfData = atob(charactersAfterChar(base64String, ','))

  // Use PDF.js to load and parse the PDF
  const pdf = await pdfjsLib.getDocument({ data: pdfData }).promise

  const totalPages = pdf.numPages
  const allTextPromises = []

  for (let pageNumber = 1; pageNumber <= totalPages; pageNumber++) {
    const pageTextPromise = pdf.getPage(pageNumber).then(function (page) {
      return page.getTextContent()
    }).then(function (textContent) {
      return textContent.items.map(item => item.str).join(' ')
    })

    allTextPromises.push(pageTextPromise)
  }

  const allTexts = await Promise.all(allTextPromises)
  const allText = allTexts.join('\n')

  return allText
}

window.dash_clientside.bulk_essay_feedback = {
  /**
   * Sends data to server via websocket
   */
  send_to_loconnection: async function (state, hash, clicks, query, systemPrompt, tags) {
    if (state === undefined) {
      return window.dash_clientside.no_update
    }
    if (state.readyState === 1) {
      if (hash.length === 0) { return window.dash_clientside.no_update }
      const decoded = decode_string_dict(hash.slice(1))
      if (!decoded.course_id) { return window.dash_clientside.no_update }

      decoded.gpt_prompt = ''
      decoded.message_id = ''

      const trig = window.dash_clientside.callback_context.triggered[0]
      if (trig.prop_id.includes('bulk-essay-analysis-submit-btn')) {
        decoded.gpt_prompt = query
        decoded.system_prompt = systemPrompt
        decoded.tags = tags
      }

      const message = {
        wo: {
          execution_dag: 'wo_bulk_essay_analysis',
          target_exports: ['gpt_bulk'],
          kwargs: decoded
        }
      }
      return JSON.stringify(message)
    }
    return window.dash_clientside.no_update
  },

  /**
   * parse message from websocket to the data and error store
   */
  receive_ws_message: function (message) {
    const data = JSON.parse(message.data).wo.gpt_bulk || [];
    if (Object.prototype.hasOwnProperty.call(data, 'error')) {
      console.error('Error received from server', data.error);
      return [[], data.error];
    }
    return [data, false];
  },

  /**
   * adds submitted query to history and clear input
   */
  update_input_history_on_query_submission: async function (clicks, query, history) {
    if (clicks > 0) {
      return ['', history.concat(query)]
    }
    return [query, window.dash_clientside.no_update]
  },

  /**
   * update history based on history browser storage
  */
  update_history_list: function (history) {
    const items = history.map((x) => {
      return {
        namespace: 'dash_html_components',
        type: 'Li',
        props: { children: x }
      }
    })
    return {
      namespace: 'dash_html_components',
      type: 'Ol',
      props: { children: items }
    }
  },

  /**
   * update student cards based on new data in storage
   */
  update_student_grid: function (message, history) {
    const currPrompt = history.length > 0 ? history[history.length - 1] : ''
    const cards = message.map((x) => {
      return createStudentCard(x, currPrompt)
    })
    return cards
  },

  /**
   * show attachment panel upon uploading document and populate fields
   *
   * updates the following
   * - extracted text from uploaded file
   * - default attachment name (based on filename)
   * - whether we show the attachment upload panel
  */
  open_and_populate_attachment_panel: async function (contents, filename, timestamp, shown) {
    if (filename === undefined) {
      return ['', '', shown]
    }
    let data = ''
    if (filename.endsWith('.pdf')) {
      data = await extractPDF(contents)
    }
    // TODO add support for docx-like files
    return [data, filename.slice(0, filename.lastIndexOf('.')), shown.concat('attachment')]
  },

  /**
   * append tag in curly braces to input
  */
  add_tag_to_input: function (clicks, curr, store) {
    const trig = window.dash_clientside.callback_context.triggered[0]
    const trigProp = trig.prop_id
    const trigJSON = JSON.parse(trigProp.slice(0, trigProp.lastIndexOf('.')))
    if (trig.value > 0) {
      return curr.concat(` {${trigJSON.index}}`)
    }
    return window.dash_clientside.no_update
  },

  /**
   * enable/disabled submit based on query
   * makes sure there is a query and the tags are properly formatted
   *
   * updates the following components
   * - submit query button disbaled status
   * - helper text for why we disabled the submit query button
  */
  disabled_query_submit: function (query, store) {
    if (query.length === 0) {
      return [true, 'Please create a request before submitting.']
    }
    const tags = Object.keys(store)
    const queryTags = query.match(/[^{}]+(?=})/g) || []
    const diffs = queryTags.filter(x => !tags.includes(x))
    if (diffs.length > 0) {
      return [true, `Unable to find [${diffs.join(',')}] within the tags. Please check that the spelling is correct or remove the extra tags.`]
    } else if (!queryTags.includes('student_text')) {
      return [true, 'Submission requires the inclusion of {student_text} to run the request over the student essays.']
    }
    return [false, '']
  },

  /**
   * enable/disable the save attachment button if tag is already in use/blank
   *
   * updates the following components
   * - save button disbaled status
   * - helper text for why we are disabled
   */
  disable_attachment_save_button: function (label, tags) {
    if (label.length === 0) {
      return [true, 'Please add a unique label to your attachment']
    } else if (tags.includes(label)) {
      return [true, `Label ${label} is already in use.`]
    }
    return [false, '']
  },

  /**
   * populate word bank of tags
   */
  update_tag_buttons: function (tagStore) {
    const tagLabels = Object.keys(tagStore)
    const tags = tagLabels.map((val) => {
      const button = {
        namespace: 'dash_bootstrap_components',
        type: 'Button',
        props: {
          children: val,
          id: { type: 'bulk-essay-analysis-tag', index: val },
          n_clicks: 0,
          size: 'sm',
          color: 'secondary'
        }
      }
      return button
    })
    return tags
  },

  /**
   * Save attachment to tag storage
   */
  save_attachment: function (clicks, label, text, tagStore, shown) {
    if (clicks > 0) {
      const newStore = tagStore
      newStore[label] = text
      return [newStore, shown.filter(item => item !== 'attachment')]
    }
    return tagStore
  },

  /**
   * Check if we've received any errors and update
   * the alert with the appropriate information
   *
   * returns an array which updates dash components
   * - text to display on alert
   * - show alert
   * - JSON error data on the alert (only in debug)
   */
  update_alert_with_error: function (error) {
    if (!error) {
      return ['', false, ''];
    }
    const text = 'Oops! Something went wrong ' +
                 "on our end. We've noted the " +
                 'issue. Please try again later, or consider ' +
                 'exploring a different dashboard for now. ' +
                 'Thanks for your patience!';
    return [text, true, error];
  }
};
