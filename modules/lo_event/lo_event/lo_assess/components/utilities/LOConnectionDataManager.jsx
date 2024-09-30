// TODO this file is untested, but goes along the with
// communication protocol changes introduced in PR #162.
// This won't do anything until that branch is merged in.
/**
 * LOConnectionDataManager handles storing and processing incoming
 * messages from the communication protocol websocket connection.
 * The communication protocol sends batches of updates to apply
 * to a clientside data object.
 *
 * When the internal data is updated, we call the `onDataUpdate`
 * parameter so parents can update accordingly.
 *
 * Usage:
 * ```js
 * const { message, } = LOConnection({ url, dataScope }); // or some other websocket
 * const handleDataUpdate = ({ dataObject, errors }) => {
 *   setUserData(dataObject);
 *   setErrors(errors);
 * };
 * return ( <LOConnectionDataManager message={message} onDataUpdate={handleDataUpdate} /> );
 * ```
 */
import { useEffect, useState } from 'react';

export const LOConnectionDataManager = ({ message, onDataUpdate }) => {
  const [dataObject, setDataObject] = useState({});
  const [errors, setErrors] = useState({});

  // TODO this function ought to be broken up into smaller functions.
  // Revisit this during testing.
  const processMessages = (messages, data) => {
    const updatedData = { ...data };
    messages.forEach((msg) => {
      const pathKeys = msg.path.split('.');
      let current = updatedData;

      // Traverse the path to get to the right location
      for (let i = 0; i < pathKeys.length - 1; i++) {
        const key = pathKeys[i];
        if (!(key in current)) {
          current[key] = {}; // Create path if it doesn't exist
        }
        current = current[key];
      }

      const finalKey = pathKeys[pathKeys.length - 1];
      if ('error' in msg.value) {
        setErrors((prevErrors) => ({
          ...prevErrors,
          [msg.path]: msg.value
        }));
      } else {
        setErrors((prevErrors) => {
          const newErrors = { ...prevErrors };
          delete newErrors[msg.path];
          return newErrors;
        });
        if (msg.op === 'update') {
          // Update the user data with new information
          current[finalKey] = {
            ...current[finalKey], // Existing data
            ...msg.value // New data (overwrites where necessary)
          };
        }
      }
    });
    return updatedData;
  };

  useEffect(() => {
    if (message) {
      try {
        const messages = JSON.parse(message.data);
        setDataObject((prevData) => processMessages(messages, prevData));
      } catch (e) {
        console.error('Failed to parse incoming message:', e);
      }
    }
  }, [message]);

  useEffect(() => {
    // Notify parent component of the updated data and errors
    onDataUpdate({ dataObject, errors });
  }, [dataObject, errors, onDataUpdate]);

  return null; // No rendering needed, just a data handler.
};
