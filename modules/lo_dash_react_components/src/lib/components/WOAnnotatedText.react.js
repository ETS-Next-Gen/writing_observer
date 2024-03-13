import React, { Component } from 'react'
import PropTypes from 'prop-types'
import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Popover from 'react-bootstrap/Popover'

import 'react-tooltip/dist/react-tooltip.css'

/**
 * WOAnnotatedText
 */
export default class WOAnnotatedText extends Component {
  constructor(props) {
    super(props)
    this.state = {
      selectedItem: null
    }
  }

  handleOverlap = (chunks, text) => {
    return chunks.reduce((prev, curr) => {
      const lastChunk = prev[prev.length - 1]
      if (lastChunk && lastChunk.end > curr.start) {
        const commonText = text.substring(curr.start, lastChunk.end)
        const remainderText = text.substring(lastChunk.end, curr.end)
        const newLastChunk = { ...lastChunk, text: text.substring(lastChunk.start, curr.start) }
        const commonChunk = {
          text: commonText,
          annotated: true,
          id: `${newLastChunk.id}-${curr.id}`,
          start: curr.start,
          end: lastChunk.end,
          tooltip: lastChunk.tooltip.concat(curr.tooltip),
          style: { ...curr.style, ...lastChunk.style }
        }
        const newChunk = {
          text: remainderText,
          annotated: true,
          id: curr.id,
          start: lastChunk.end,
          end: curr.end,
          tooltip: curr.tooltip,
          style: curr.style
        }
        return [...prev.slice(0, prev.length - 1), newLastChunk, commonChunk, newChunk]
      } else {
        return [...prev, curr]
      }
    }, [])
  }

  replaceNewLines = (str) => {
    const split = str.split('\n')
    if (split.length > 1) {
      return split.map((line, index) => (
        <React.Fragment key={index}>
          {line}
          {split.length-1 === index ? <span/> : <br/>}
        </React.Fragment>
      ))
    }
    return str
  }

  render() {
    const { breakpoints, text, className } = this.props
    const sortedList = [...breakpoints].sort((a, b) => a.start - b.start)
    let chunks = sortedList.reduce((prev, { start, offset, tooltip, style }, index) => {
      const lastOffset = prev.length ? prev[prev.length - 1].end : 0
      if (start > lastOffset) {
        prev.push({
          text: text.substring(lastOffset, start),
          annotated: false
        })
      }
      prev.push({
        text: text.substring(start, start + offset),
        annotated: true,
        id: index,
        start: start,
        end: start + offset,
        tooltip: [tooltip],
        style: style
      })
      return prev
    }, [])

    chunks = this.handleOverlap(chunks, text)

    if (chunks.length === 0) {
      return <div className={className}>
        {this.replaceNewLines(text)}
      </div>
    }

    // TODO figure out how empty breakpoints
    if (chunks[chunks.length - 1].end < text.length) {
      chunks.push({
        text: text.substring(chunks[chunks.length - 1].end),
        annotated: false
      })
    }
    return (
      <div className={className}>
        {chunks.map((chunk, index) => (
          chunk.annotated
            ?
            <OverlayTrigger
              key={index}
              placement='bottom'
              overlay={
                <Popover>
                  <Popover.Header as="h3">Annotations</Popover.Header>
                  <Popover.Body>
                    {chunk.tooltip}
                  </Popover.Body>
                </Popover>
              }
            >
              <span
                style={chunk.style}
              >
                {this.replaceNewLines(chunk.text)}
              </span>
            </OverlayTrigger>
            : <span key={index}>
              {this.replaceNewLines(chunk.text)}
            </span>
        ))}
      </div>
    )
  }
}

WOAnnotatedText.defaultProps = {
  id: '',
  className: '',
  text: '',
  breakpoints: []
}

WOAnnotatedText.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * The breakpoints of our text
   */
  breakpoints: PropTypes.arrayOf(PropTypes.exact({
    id: PropTypes.string,
    start: PropTypes.number,
    offset: PropTypes.number,
    tooltip: PropTypes.node,
    style: PropTypes.object
  })),

  /**
   * Text of essay
   */
  text: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func
}
