/**
 * General scripts used for the bulk essay analysis dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {}
}

const createStudentCard = function (student) {
  const header = {
    namespace: 'dash_bootstrap_components',
    type: 'CardHeader',
    props: { children: student.profile.name.full_name }
  }
  const studentText = {
    namespace: 'lo_dash_react_components',
    type: 'WOAnnotatedText',
    props: { text: student.text, breakpoints: [] }
  }
  const feedback = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: student?.feedback ? student.feedback : '',
      className: student?.feedback ? 'border-start p-1 overflow-auto' : '',
      style: { whiteSpace: 'pre-line' }
    }
  }
  const body = {
    namespace: 'lo_dash_react_components',
    type: 'LOPanelLayout',
    props: {
      children: studentText,
      panels: [{ children: feedback, id: 'feedback-text', width: '40%' }],
      shown: feedback.props.children.length > 0 ? ['feedback-text'] : [],
      className: 'overflow-auto p-1'
    }
  }
  const card = {
    namespace: 'dash_bootstrap_components',
    type: 'Card',
    props: {
      children: [header, body],
      style: { maxHeight: '300px' }
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

const createChatCard = function (chat, user) {
  const teacher = (user === 'teacher')
  const card = {
    namespace: 'dash_bootstrap_components',
    type: 'Card',
    props: { children: chat, body: true, color: teacher ? '#6cc3d540' : '#fff' }
  }
  return {
    namespace: 'dash_bootstrap_components',
    type: 'Col',
    props: {
      children: card,
      align: teacher ? 'end' : 'start',
      width: 9
    }
  }
}

window.dash_clientside.bulk_essay_feedback = {
  send_to_loconnection: async function (state, hash, clicks, query) {
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

  update_ui_upon_query_submission: async function (clicks, text, children) {
    if (clicks > 0) {
      const loading = {
        namespace: 'dash_bootstrap_components',
        type: 'Col',
        props: {
          children: {
            namespace: 'dash_bootstrap_components',
            type: 'Spinner',
            props: { color: 'primary' }
          },
          align: 'start',
          width: 8,
          id: 'loading'
        }
      }
      const newChildren = [loading, createChatCard(text, 'teacher')].concat(children)
      return ['', newChildren]
    }
  },

  update_student_grid: function (message) {
    const cards = message.map((x) => {
      return createStudentCard(x)
    })
    return cards
  },

  add_response_to_chat: function (message, children) {
    const chatCard = createChatCard('Your feedback will appear next to each student card.', 'gpt')
    const index = children.findIndex(item => item.props.id === 'loading')
    if (index > -1) {
      children[index] = chatCard
    }
    return children
  }
}
