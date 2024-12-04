import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';

import LONameTag from './LONameTag.react';

function createGoogleDocumentURL (docId) {
  return `https://docs.google.com/document/d/${docId}`;
}

/**
 * WOStudentTextTile
 */
export default class WOStudentTextTile extends Component {
  constructor (props) {
    super(props);
    this.handleDocumentSelectChange = this.handleDocumentSelectChange.bind(this);
  }

  handleDocumentSelectChange (event) {
    this.props.setProps({ selectedDocument: event.target.value });
  }

  render () {
    const { id, className, style, showHeader, studentInfo, selectedDocument, currentOptionHash, childComponent } = this.props;
    // HACK we need to pass the appropriate student information into the child component
    childComponent.props._dashprivate_layout.props = { ...studentInfo.documents[selectedDocument] };

    const documentIsSelected = selectedDocument && studentInfo.documents[selectedDocument];
    const isLoading = documentIsSelected && currentOptionHash !== studentInfo.documents[selectedDocument].optionHash;
    let bodyClassName = isLoading ? 'loading' : '';
    bodyClassName = `${bodyClassName} overflow-auto position-relative`;

    const loadedItem = documentIsSelected
      ? <>{childComponent}</>
      : <div>Document information not found.</div>;

    // TODO the chunk of commented code allows for linking directly to the selected document
    // and allows the user to select which document they wish to see at a given moment.
    // Neither of these features are currently available due to limitations with the communication
    // protocol. For now they are being commented out so users are not inclined to use them.
    return (
      <Card key={`WOStudentTextTile-${id}`} className={`WOStudentTextTile ${className}`} style={style} id={id}>
        <Card.Header className={showHeader ? '' : 'd-none'}>
          <LONameTag
            id='lo-name-tag'
            profile={studentInfo.profile || {}}
            includeName={true}
          />
          {/* <a
            href={createGoogleDocumentURL(selectedDocument)}
            target='_blank'
            className={selectedDocument ? '' : 'd-none'}
          >
            <i className='fas fa-up-right-from-square'/>
          </a>
          <Form.Select value={selectedDocument || ''} onChange={this.handleDocumentSelectChange}>
            <option value='' disabled>
              Please select a document
            </option>
            {studentInfo.availableDocuments.map(doc => (
              <option key={doc.id} value={doc.id}>{doc.title}</option>
            ))}
          </Form.Select> */}
        </Card.Header>
        {isLoading && (
          <div className='position-absolute top-0 end-0 bg-light p-1 d-flex border border-1 border-top-0 rounded-bottom'>
            <div className='loading-circle me-1'/>
            <span>Loading...</span>
          </div>
        )}
        <Card.Body className={bodyClassName}>
          {loadedItem}
        </Card.Body>
      </Card>
    );
  }
}

WOStudentTextTile.defaultProps = {
  className: '',
  showHeader: true,
  style: {},
  studentInfo: {
    profile: {},
    availableDocuments: [],
    documents: {}
  }
};

WOStudentTextTile.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * Style to apply to the outer most item. This
   * is usually used to set the size of the tile.
   */
  style: PropTypes.object,

  /**
   * Determine whether the header with the student
   * name should be visible or not
   */
  showHeader: PropTypes.bool,

  /**
   * Which document is currently selected for this student
   */
  selectedDocument: PropTypes.string,

  /**
   * Hash of the current options, used to determine if we
   * should be in a loading state or not.
   */
  currentOptionHash: PropTypes.string,

  /**
   * Component to use for within the card body
   */
  childComponent: PropTypes.node,

  /**
   * The breakpoints of our text
   */
  studentInfo: PropTypes.exact({
    profile: PropTypes.object,
    availableDocuments: PropTypes.arrayOf(PropTypes.exact({
      id: PropTypes.string,
      title: PropTypes.string
    })),
    documents: PropTypes.object
    // objectOf(
    //   PropTypes.shape({
    //     text: PropTypes.string,
    //     breakpoints: PropTypes.arrayOf(PropTypes.any),
    //     optionHash: PropTypes.string
    //   })
    // )
  }),

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func
};
