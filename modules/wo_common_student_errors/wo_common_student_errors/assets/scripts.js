if (!window.dash_clientside) {
  window.dash_clientside = {}
}

const categoryColors = {
  Error: 'white', // white
  Capitalization: '#f3969a', // light pink
  Grammar: '#56cc9d', // turquoise
  'Possible Typo': '#6cc3d5', // sky blue
  Punctuation: '#ffce67', // yellow
  Semantics: '#ff7851', // orange
  Spelling: '#D9A9F5', // lilac purple
  Style: '#9EF5D9', // mint green
  Typography: '#87CEEB', // baby blue
  Usage: '#FFB347', // soft orange
  'Word Boundaries': '#F5F0A9' // light yellow
}

window.dash_clientside.common_student_errors = {
  send_to_loconnection: function (state, hash) {
    /**
     * When the hash of the URL changes, we send an updated query
     * to the Learning Observer server.
     */
    if (state === undefined) {
      return [window.dash_clientside.no_update, 'individual-student-loading']
    }
    if (state.readyState === 1) {
      if (hash.length === 0) { return window.dash_clientside.no_update }
      const decoded = decode_string_dict(hash.slice(1))
      // TODO handle no course id better
      if (!decoded.course_id) { return window.dash_clientside.no_update }

      // the server expects a list of dictionary students, so we format the data that way
      let loadingClass = 'individual-student-loaded'
      if ('student_id' in decoded) {
        decoded.student_id = [{ user_id: decoded.student_id }]
        loadingClass = 'individual-student-loading'
      } else {
        decoded.student_id = []
      }
      const message = {
        wo: {
          execution_dag: 'writing_observer',
          target_exports: ['activity', 'single_student', 'overall_errors'],
          kwargs: decoded
        }
      }
      return [JSON.stringify(message), loadingClass]
    }
    return [window.dash_clientside.no_update, window.dash_clientside.no_update]
  },

  update_hash_via_graph: function (selected, message) {
    /**
     * Updated the selected student in the URL hash
     */
    if (selected == null) { return window.dash_clientside.no_update }
    const pt = selected.points[0]
    const data = message.wo.lt_combined[pt.pointIndex]
    const params = decode_string_dict(window.location.hash.slice(1))
    return `#course_id=${params.course_id};student_id=${data.user_id}`
  },

  receive_populate_activity: function (message) {
    const data = message.wo.activity_combined
    if (!data) {
      return ['No students', 'No students']
    }
    const params = decode_string_dict(window.location.hash.slice(1))
    const output = {}
    let badge = {}
    for (let i = 0; i < data.length; i++) {
      badge = {
        namespace: 'dash_html_components',
        type: 'A',
        props: {
          href: `#course_id=${params.course_id};student_id=${data[i].user_id}`,
          className: 'activity-status-link',
          children: {
            namespace: 'lo_dash_react_components',
            props: {
              profile: data[i].profile,
              className: 'student-name-tag',
              id: `${data[i].user_id}-activity-img`
            },
            type: 'LONameTag'
          }
        }
      }
      output[data[i].status] = output[data[i].status] === undefined ? [badge] : output[data[i].status].concat(badge)
    }
    return [output.inactive === undefined ? 'No students' : output.inactive, output.active === undefined ? 'No students' : output.active]
  },

  receive_populate_student_error: function (message, hash) {
    let data = message.wo.single_lt_combined
    if (!data | data.length === 0) {
      return ['Select a student', '']
    }
    data = data[0]
    const decoded = decode_string_dict(hash.slice(1))
    if (decoded.student_id !== data.user_id) {
      return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, 'individual-student-loading']
    }
    const student = {
      namespace: 'lo_dash_react_components',
      props: {
        profile: data.profile,
        className: 'student-name-tag',
        id: `${data.user_id}-activity-img`,
        includeName: true
      },
      type: 'LONameTag'
    }
    const text = data.text.split('\n').map((x) => {
      return {
        namespace: 'dash_html_components',
        type: 'P',
        props: { children: x }
      }
    })
    const errors = data.matches.map((x) => {
      return {
        namespace: 'dash_bootstrap_components',
        type: 'Card',
        props: {
          children: x.message,
          body: true,
          color: `${categoryColors[x.label]}80`,
          class_name: 'bg-opacity-25'
        }
      }
    })
    let names = ['Errors']
    let ids = ['Errors']
    let parents = ['']
    let values = [data.matches.length]
    for (let key in data.category_counts) {
      ids = ids.concat(key)
      names = names.concat(key)
      parents = parents.concat('Errors')
      values = values.concat(data.category_counts[key])
    }
    let category
    for (let key in data.subcategory_counts) {
      category = key.split(':')[0]
      ids = ids.concat(key)
      names = names.concat(key.split(':')[1].trim())
      parents = parents.concat(category)
      values = values.concat(data.subcategory_counts[key])
    }
    const extendedData = [{ ids: [ids], labels: [names], parents: [parents], values: [values] }, [0], names.length]
    return [student, text, errors, extendedData, 'individual-student-loaded']
  },

  receive_populate_error_graph: function (message) {
    const data = message.wo.lt_combined
    if (!data) {
      return window.dash_clientside.no_update
    }
    const len = data.length
    let x = []
    let y = []
    let labels = []
    for (let i = 0; i < len; i++) {
      x = x.concat(data[i].wordcounts.tokens)
      y = y.concat(data[i].matches.length)
      labels = labels.concat(`${data[i].profile.name.given_name.slice(0, 1)}${data[i].profile.name.family_name.slice(0, 1)}`)
    }
    return [
      { x: [x], y: [y], text: [labels] },
      [0],
      len
    ]
  },

  update_graph_hover: function (hoverData, message) {
    if (!hoverData) {
      return [false, window.dash_clientside.no_update, '']
    }
    const pt = hoverData.points[0]
    const data = message.wo.lt_combined[pt.pointIndex]
    const child = {
      namespace: 'dash_html_components',
      type: 'Div',
      props: {
        className: 'errors-per-word-tooltip',
        children: [
          {
            namespace: 'lo_dash_react_components',
            props: {
              profile: data.profile,
              id: `${data.user_id}-activity-img`,
              includeName: true
            },
            type: 'LONameTag'
          },
          {
            namespace: 'dash_html_components',
            type: 'P',
            props: {
              children: `Errors: ${data.matches.length}\nWords: ${data.wordcounts.tokens}`
            }
          }
        ]
      }
    }
    return [true, pt.bbox, child]
  },

  receive_populate_categorical_errors: function (message) {
    const data = message.wo.lt_combined
    if (!data) {
      return window.dash_clientside.no_update
    }
    const rows = []

    data.forEach(student => {
      // TODO we could wrap this in a link component to adjust the side view
      let columnData = [{
        namespace: 'dash_html_components',
        type: 'Td',
        props: { 
          children: {
            namespace: 'lo_dash_react_components',
            props: {
              profile: student.profile,
              id: `${student.user_id}-activity-img`
            },
            type: 'LONameTag'
          }
        }
      }]
      for (let category in categoryColors) {
        let value = ''
        if (category === 'Error') {
          value = student.matches.length
        } else {
          value = student.category_counts[category]
        }
        columnData.push({
          namespace: 'dash_html_components',
          type: 'Td',
          props: { children: value, style: { backgroundColor: `${categoryColors[category]}80` } }
        })
      }
      rows.push({
        namespace: 'dash_html_components',
        type: 'Tr',
        props: {
          children: columnData
        }
      })
    })
    return rows
  },

  receive_populate_agg_info: function (message) {
    const data = message.wo.lt_combined
    if (!data) {
      return window.dash_clientside.no_update
    }

    const flatErrors = data.map((student) => {
      return {
        student: { user_id: student.user_id, profile: student.profile },
        errors: student.matches.map((match) => {
          return {
            category: match.label,
            subcategory: match.detail,
            shortMessage: match.shortMessage,
            message: match.message
          }
        })
      }
    })
    return flatErrors
  }
}
