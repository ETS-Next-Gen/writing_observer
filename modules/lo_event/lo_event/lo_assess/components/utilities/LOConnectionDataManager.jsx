// TODO this file is untested, but goes along the with 
// communication protocol changes introduced in PR #162.
// This won't do anything until that branch is merged in.
import React, { useEffect, useState } from 'react';

export const LOConnectionDataManager = ({ message, onDataUpdate }) => {
  const [userData, setUserData] = useState({});
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (message) {
      try {
        const messages = JSON.parse(message.data);
        setUserData((prevData) => {
          const updatedData = { ...prevData };
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
                [msg.path]: msg.value,
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
                  ...msg.value, // New data (overwrites where necessary)
                };
              }
            }
          });
          return updatedData;
        });
      } catch (e) {
        console.error('Failed to parse incoming message:', e);
      }
    }
  }, [message]);

  useEffect(() => {
    // Notify parent component of the updated data and errors
    onDataUpdate({ userData, errors });
  }, [userData, errors, onDataUpdate]);

  return null; // No rendering needed, just a data handler.
};
