import React, {useState} from 'react';
import PropTypes from 'prop-types';
import { Arrow, LEFT, updateArrowPositions, initArrows } from './helperlib'

/* Gives information about one card for one student. */
function ZPDItemCard(props) {
  const halfCircle = 180;
  const cardAngle = halfCircle * (props.card_index+1) / (props.card_count+1);
  const cardOffsetRadius = 0.8;
  return (
    <div className="item-card" id={props.id}>
      <div className="card-header">{props.item_name}</div>
      <div className="card-table">
        <div className="card-row">
          <div className="card-cell" title="Visited">Visited</div>
          <div className="card-cell" title="Attempts">Attempts</div>
          <div className="card-cell" title="Supports">Supports</div>
        </div>
        <div className="card-row">
          <div className="card-cell" title="Visited">{props.visited ? "✓" : "X"}</div>
          <div className="card-cell" title="Attempts">{props.attempts}</div>
          <div className="card-cell" title="Supports">{props.supports}</div>
        </div>
      </div>
      <Arrow
      	source={props.id}
      	sourceOffset={LEFT}
      	target="end"
      	targetOffset={[cardOffsetRadius, cardAngle]}
      />
    </div>
  );
}

ZPDItemCard.propTypes = {
  card_index: PropTypes.number.isRequired,
  card_count: PropTypes.number.isRequired,
  id: PropTypes.number.isRequired,
  item_name: PropTypes.string.isRequired,
  visited: PropTypes.bool.isRequired,
  attempts: PropTypes.number.isRequired,
  supports: PropTypes.number.isRequired,
};

/* Static display of the three zones */
const ZPDRing = (_props) => {
  return (
    <div className="left-column">
      <div className="znd-circle">
	      <div className="label znd-circle-label">Can't do</div>
        <div className="zpd-circle">
	        <div className="zpd-label zpd-circle-label">Zone of Proximal Development</div>
	        <div className="zad-circle" id="end">
	          <div className="label">Mastery</div>
	        </div>
        </div>
      </div>
    </div>
  );
}

const ZPDHeader = (props) => {
  const [showDropdown, setShowDropdown] = useState(false);

  const dummy_names = ["Bob", "Sue", "Jill", "Jack"];

  const handleClick = () => {
    setShowDropdown(!showDropdown);
  };

  const handleSelect = (name) => {
    props.setStudentName(name);
    setShowDropdown(false);
  };

  return (
    <header className="nav-header">
      <div className="button-left">
	<button className="button">&lt;</button>
      </div>
      <div className="header-student" onClick={handleClick}>{props.student_name}</div>
      {showDropdown && (
        <ul className="dropdown">
          {dummy_names.map((name) => (
            <li
              key={name}
              onClick={() => handleSelect(name)}
              className={
                name === props.student_name
                  ? 'dropdown-item dropdown-item-selected'
                  : 'dropdown-item'
              }
            >
              {name}
            </li>
          ))}
        </ul>
      )}
      <div className="button-right">
	<button className="button">&gt;</button>
      </div>
    </header>
  );
}

ZPDHeader.propTypes = {
  student_name: PropTypes.string.isRequired,
  setStudentName: PropTypes.func.isRequired,
};

export default class ZPDPlot extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      student_name: props.student_name,
    };
    this.setStudentName = this.setStudentName.bind(this);
  }

  setStudentName(new_name) {
    this.setState({ student_name: new_name });
    this.props.setProps({ student_name: new_name });
  }

  componentDidMount() {
    updateArrowPositions();
  }

  render() {
    const { ZPDItemCards } = this.props;

    return (
      <div id="zpd-wrapper" className="zpd-wrapper arrow-wrapper">
        <ZPDHeader
          setStudentName={this.setStudentName}
          student_name={this.state.student_name}
        />
        <ZPDRing id="ring" />
        <div id="zpd-wrapper">
          <div className="right-column">
            {ZPDItemCards.map((card, index) => (
              <ZPDItemCard
                key={card.id}
                card_index={index}
                card_count={ZPDItemCards.length}
                {...card}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }
}

ZPDPlot.defaultProps = {};

ZPDPlot.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    ZPDItemCards: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        item_name: PropTypes.string,
        zone: PropTypes.string,
        attempts: PropTypes.string,
        supports: PropTypes.string,
        visited: PropTypes.bool
    })).isRequired,
    /**
     * The value displayed in the input.
     */
    student_name: PropTypes.string,
    value: PropTypes.string,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func
};

initArrows();
