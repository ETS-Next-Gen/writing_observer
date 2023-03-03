import React, {Component} from 'react';
import PropTypes from 'prop-types';


/**
 */
export default class StudentSelectHeader extends Component {
    constructor(props) {
        super(props);
        this.state = {
            showDropdown: false
        }
    }

    handleClick() {
        this.setState({ showDropdown: !this.state.showDropdown })
    };

    handleSelect(name) {
        this.props.setStudentName(name);
        this.setState({ showDropdown: false })
    };

    render() {
        const {id, class_name, students, selected} = this.props;
        const {showDropdown} = this.state;
        console.log(students)
    
        return (
            <header id='student-select-header' className="nav-header">
                <div className="button-left">
                    <button className="button">&lt;</button>
                </div>
                <div className="header-student" onClick={() => this.handleClick()}>{selected}</div>
                {showDropdown && (
                    <ul className="dropdown">
                        {students.map((name) => (
                            <li
                                key={name}
                                onClick={() => this.handleSelect(name)}
                                className={
                                name === selected
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
}

StudentSelectHeader.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    class_name: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    students: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    selected: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    setStudentName: PropTypes.func
}
