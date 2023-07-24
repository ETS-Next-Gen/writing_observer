import React, { Component } from "react";
import PropTypes from "prop-types";

/**
 * LONameTag provides the image and name pair for a given profile
 */
export default class LONameTag extends Component {
    render() {
        const { id, profile, className, includeName } = this.props;
        return (
            <div
                key={`lo-name-tag-${id}`}
                className={`LONameTag ${className}`}
                id={id}
            >
                {
                    (profile.photo_url & profile.photo_url !== '//lh3.googleusercontent.com/a/default-user')
                    ? <img className='name-tag-photo' src={`https:${profile.photo_url}`} title={profile.name.full_name} />
                    : <span className='name-tag-photo' title={profile.name.full_name}>{`${profile.name.given_name.slice(0,1)}${profile.name.family_name.slice(0,1)}`}</span>
                }
                {includeName ? <span className='name-tag-name'>{profile.name.full_name}</span> : <span/>}
            </div>
        )
    }
}
LONameTag.defaultProps = {
    id: "",
    className: "",
    includeName: false
};

LONameTag.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    className: PropTypes.string,

    /**
       * System profile object
       * `{
              email_address: "example@example.com",
              name: {
                family_name: "Doe",
                full_name: "John Doe",
                given_name: "John"
              },
              photo_url: "//lh3.googleusercontent.com/a/default-user"
          }`
       */
    profile: PropTypes.object.isRequired,

    /**
     * Include name or just use the image
     */
    includeName: PropTypes.bool,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,
};
