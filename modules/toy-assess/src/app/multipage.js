/*
 * This is old code for navigating between pages. It worked before,
 * and we might want it again.
 *
 * However, we are currently not using it, and have no way to test
 * it.
 *
 * As of when we removed it, this worked fine except for the missing
 * imports.
 */

export const NAVIGATE = 'NAVIGATE';

// Which page are we on?
export function activePage() {
  return useApplicationSelector(s => s?.page || "Home");
}

registerReducer(NAVIGATE, (state = initialState, action) => {
  dclog("Register reducer:", action);
    return {
	...state,
	'page': action.target
    };
});

function navigation(id, target) {
  return () => lo_event.logEvent(NAVIGATE, {id, target});
}

export function NavigateButton({id, target, children}) {
  return (
    <Button onClick={navigation(id, target)}>
      { children }
    </Button>
  );
}
