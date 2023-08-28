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
    let pageTextPromise = pdf.getPage(pageNumber).then(function (page) {
      return page.getTextContent()
    }).then(function (textContent) {
      return textContent.items.map(item => item.str).join(' ')
    })

    allTextPromises.push(pageTextPromise)
  }

  const allTexts = await Promise.all(allTextPromises)
  const allText = allTexts.join(' ')

  return allText
}

window.dash_clientside.bulk_essay_feedback = {
  send_to_loconnection: async function (state, hash, clicks, query, systemPrompt, rubricText) {
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
        decoded.rubric = rubricText
      }

      const message = {
        wo: {
          execution_dag: 'writing_observer',
          target_exports: ['gpt_bulk'],
          kwargs: decoded
        }
      }
      return JSON.stringify(message)
    }
    return window.dash_clientside.no_update
  },

  update_input_history_on_query_submission: async function (clicks, query, history) {
    if (clicks > 0) {
      return ['', history.concat(query)]
    }
  },

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

  update_student_grid: function (message, history) {
    const currPrompt = history.length > 0 ? history[history.length - 1] : ''
    const cards = message.map((x) => {
      return createStudentCard(x, currPrompt)
    })
    return cards
  },

  update_rubric: async function (contents, filename) {
    if (filename === undefined) {
      return ['', '']
    }
    let data = ''
    if (filename.endsWith('.pdf')) {
      data = await extractPDF(contents)
    }
    return [data, `Current: ${filename}`]
  }
}
