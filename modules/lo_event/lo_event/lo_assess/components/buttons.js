import * as reduxLogger from '../../reduxLogger.js';

export function Button( {...props} ) {
  const className = props.className ?? "blue-button";
  return <button className={className} {...props}/>;
}

export function ResetButton({children, ...props}) {
  return (
    <Button onClick={() => reduxLogger.setState({})} {...props} >
      { children }
    </Button>
  );
}

