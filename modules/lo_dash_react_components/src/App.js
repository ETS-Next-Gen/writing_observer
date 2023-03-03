import logo from './logo.svg';
import './App.css';

import './css/styles.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import { LOConnection, LOMetrics, LOIndicatorBars, StudentSelectHeader } from './lib'

function App() {
  return (
    <div className="App">
      < StudentSelectHeader students={['Bart', 'Lisa', 'Milhouse']} selected='Bart'/>
      < LOConnection />
      < LOMetrics
        data={{
            "sentences": {
                "id": "sentences",
                "value": 33,
                "label": " sentences"
            },
            "paragraphs": {
                "id": "paragraphs",
                "value": 45,
                "label": " paragraphs"
            },
        }}
        shown={["paragraphs", "sentences"]}
      />
      < LOIndicatorBars
        data={{
            "sentences": {
                "id": "sentences",
                "value": 33,
                "label": " bananas"
            },
            "paragraphs": {
                "id": "paragraphs",
                "value": 45,
                "label": " paragraphs"
            },
        }}
        shown={["paragraphs", "sentences"]}
      />
      
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Editing <code>src/App.js</code> and save to reload and this changes.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
