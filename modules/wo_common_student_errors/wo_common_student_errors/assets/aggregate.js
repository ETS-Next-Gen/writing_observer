if (!window.dash_clientside) {
  window.dash_clientside = {}
}

const sortObject = function(obj) {
  const entries = Object.entries(obj)
  entries.sort((a, b) => b[1] - a[1])

  const sortedKeys = entries.map(entry => entry[0])
  const sortedValues = entries.map(entry => entry[1])
  return [sortedKeys, sortedValues]
}

const graphUpdates = function (data) {
  const sorted = sortObject(data)
  const updates = [
    { x: [sorted[0]], y: [sorted[1]] },
    [0],
    sorted[0].length
  ]
  return updates
}

const listUpdates = function (data) {
  const sorted = sortObject(data)
  const updates = []
  for (let i = 0; i < sorted[0].length; i++) {
    updates.push({
      namespace: 'dash_html_components',
      type: 'Li',
      props: { children: `${sorted[0][i]} - ${sorted[1][i]}` }
    })
  }
  return updates
}

window.dash_clientside.aggregate_common_errors = {
  update_category_graph: function (data, catClick, subcatClick) {
    const clickedCats = catClick?.points ? catClick.points.map(point => point.x) : Object.keys(categoryColors)
    const clickedSubcats = subcatClick?.points ? subcatClick.points.map(point => point.x) : []
    const categoryCount = {}
    const subcategoryCount = {}
    const feedbackCount = {}
    const studentCount = {}
    data.forEach((student) => {
      student.errors.forEach((error) => {
        categoryCount[error.category] = (categoryCount[error.category] || 0) + 1
        if (clickedCats.includes(error.category) & (clickedSubcats.length === 0 | clickedSubcats.includes(error.subcategory))) {
          subcategoryCount[error.subcategory] = (subcategoryCount[error.subcategory] || 0) + 1
          feedbackCount[error.shortMessage] = (feedbackCount[error.shortMessage] || 0) + 1
          studentCount[student.student.user_id] = (studentCount[student.student.user_id] || 0) + 1
        }
      })
    })
    return [graphUpdates(categoryCount), graphUpdates(subcategoryCount), listUpdates(feedbackCount), listUpdates(studentCount)]
  }
}
