export function getStorageMetadata(storage, keys = null) {
  if (!storage) {
    return null;
  }

  try {
    const items = {};
    
    // If no keys provided, get all items
    if (!keys) {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        try {
          items[key] = storage.getItem(key);
        } catch (e) {
          items[key] = {
            type: 'error',
            error_type: e.name || 'Unknown',
            error_message: e.message || ''
          };
        }
      }
    } 
    // Otherwise, only get specified keys
    else {
      keys.forEach(key => {
        try {
          items[key] = storage.getItem(key);
        } catch (e) {
          items[key] = {
            type: 'error',
            error_type: e.name || 'Unknown',
            error_message: e.message || ''
          };
        }
      });
    }

    return items;
  } catch (e) {
    return null; // Return null if storage is not accessible
  }
}

export const localStorageInfo = (keys = null) => ({
  name: 'localStorageInfo',
  func: () => getStorageMetadata(typeof window !== 'undefined' ? window.localStorage : null, keys),
  async: false,
  static: false // Not static as storage can change
});

export const sessionStorageInfo = (keys = null) => ({
  name: 'sessionStorageInfo',
  func: () => getStorageMetadata(typeof window !== 'undefined' ? window.sessionStorage : null, keys),
  async: false,
  static: false
});
