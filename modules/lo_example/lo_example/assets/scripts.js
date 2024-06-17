/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

// Initialize the `dash_clientside` object if it doesn't exist
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.lo_example = {
  /**
   * Send updated queries to the communication protocol.
   * @param {object} wsReadyState LOConnection status object
   * @param {string} urlHash query string from hash for determining course id
   * @returns stringified json object that is sent to the communication protocl
   */
  sendToLOConnection: async function (wsReadyState, urlHash) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update
    }
    if (wsReadyState.readyState === 1) {
      if (urlHash.length === 0) { return window.dash_clientside.no_update }
      const decodedParams = decode_string_dict(urlHash.slice(1))
      if (!decodedParams.course_id) { return window.dash_clientside.no_update }
      const outgoingMessage = {
        lo_example_query: {
          execution_dag: 'lo_example',
          target_exports: ['student_event_counts'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  /**
   * Process a message from LOConnection
   * @param {object} incomingMessage object received from LOConnection
   * @returns parsed data to local storage
   */
  receiveWSMessage: async function (incomingMessage) {
    // TODO the naming here is broken serverside. Notice above we
    //  called the target export `student_event_counts`, i.e. the named
    // export. Below, we need to call `events_join_roster`, i.e. the name
    // of the node. This ought to be cleaned up in the communication protocl.
    const messageData = JSON.parse(incomingMessage.data).lo_example_query.events_join_roster || [];
    if (messageData.error !== undefined) {
      console.error('Error received from server', messageData.error);
      return [];
    }
    return messageData;
  },

  /**
   * Build the student UI components based on the stored websocket data
   * @param {*} wsStorageData information stored in the websocket store
   * @returns Dash object to be displayed on page
   */
  populateOutput: function(wsStorageData) {
    if (!wsStorageData) {
      return 'No students';
    }
    let output = []
    // Iterate over students and create UI items for each
    for (const student of wsStorageData) {

      // We define Dash components in JS via a dictionary
      // of where the component lives, what it is, and any
      // parameters we want to pass along to it.
      // - `namespace`: the module the component is in
      // - `type`: the component to use
      // - `props`: any parameters the component expects
      // The following produces a LONameTag and Span wrapped in a Div
      studentBadge = {
        namespace: 'dash_html_components',
        type: 'Div',
        props: {
          children: [{
            namespace: 'lo_dash_react_components',
            props: {
              profile: student.profile,
              className: 'student-name-tag',
              includeName: true,
              id: `${student.user_id}-activity-img`
            },
            type: 'LONameTag'
          },{
            namespace: 'dash_html_components',
            props: {
              children: ` - ${student.count} events`,
            },
            type: 'Span'

          }]
        }
      }
      output = output.concat(studentBadge)
    }
    return output;
  }
}
