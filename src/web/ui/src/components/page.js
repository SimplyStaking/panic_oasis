import React from 'react';
import Spinner from 'react-bootstrap/Spinner';
import {
  ToastsContainer,
  ToastsContainerPosition,
  ToastsStore,
} from 'react-toasts';
import { forbidExtraProps } from 'airbnb-prop-types';
import PropTypes from 'prop-types';
import '../style/style.css';

function Page({ spinnerCondition, component }) {
  return (
    <div>
      {
        spinnerCondition
          ? (
            <div className="div-spinner-style">
              <Spinner
                animation="border"
                role="status"
                className="spinner-style"
              />
            </div>
          )
          : component
      }
      <ToastsContainer
        store={ToastsStore}
        position={ToastsContainerPosition.TOP_CENTER}
        lightBackground
      />
    </div>
  );
}

Page.propTypes = forbidExtraProps({
  spinnerCondition: PropTypes.bool.isRequired,
  component: PropTypes.oneOfType([
    PropTypes.symbol, PropTypes.object,
  ]).isRequired,
});

export default Page;
