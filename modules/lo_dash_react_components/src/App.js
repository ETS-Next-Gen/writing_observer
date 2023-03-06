import React, { Component } from "react";
import { BrowserRouter, Link, Routes, Route } from 'react-router-dom';

import "./App.css";

import "./css/styles.css";
import "bootstrap/dist/css/bootstrap.min.css";

const components = {};
const noop = ()=>null;

// Import all components and their respective test data dynamically
const importAll = (r) => {
  r.keys().forEach((key) => {
    const componentName = key.replace('./', '').replace('.react.js', '');
    components[componentName] = {
      component: r(key).default,
      testdata: testData(componentName)
    };
  });
};

// Load test data for the component, if available
function testData(component_name) {
  let testData = {};
  try {
    testData = require(`./lib/components/${component_name}.testdata.js`).default;
  } catch (error) {
    noop();
  }
  return testData;
}

importAll(require.context('./lib/components', true, /\.react.js$/));

// Display a list of installed components for navigation
function ComponentList(_props) {
  return (
    <div>
      <hr/>
      <h1>Component list</h1>
      <ul>
        {Object.entries(components).map(([name, _component]) => (
          <li key={"li_"+name}> <Link to={"/components/"+name}  key={"a_"+name}>{name}</Link> </li>
        ))}
      </ul>
   </div>
  );
}

class App extends Component {
  constructor() {
    super();
    this.state = {
      selected: "Bart",
    };
    this.setProps = this.setProps.bind(this);
  }

  setProps(newProps) {
    this.setState(newProps);
  }

  render() {
    return (
      <div>
        <BrowserRouter>
          <Routes>
            <Route path="/" key="home" element={<ComponentList/>}/>
            {Object.entries(components).map(([name, component]) => (
              <Route
                key={name}
                path={"/components/"+name}
                element={(<div>{React.createElement(component.component, component.testdata)}<ComponentList/></div>)}
              />
            ))}
          </Routes>
        </BrowserRouter>
      </div>
    );
  }
}

export default App;
// function App() {
//   const defaultProps = {
//     students: ["Bart", "Lisa", "Milhouse"],
//     selected: 'Bart',
//     label: "Yellow!"
//   };
//   const [state, setState] = useState(() => {
//     const initialState = {};
//     Object.entries(StudentSelectHeader.propTypes)
//       .filter(([prop, value]) => prop !== "setProps")
//       .forEach(([prop, value]) => {
//         initialState[prop] = value.isRequired ? null : undefined;
//         if (defaultProps.hasOwnProperty(prop)) {
//           initialState[prop] = defaultProps[prop];
//         }
//       });
//     // console.log(initialState);
//     return initialState;
//   });
//   const setProps = (newProps) => {
//     setState((prevState) => {
//       return { ...prevState, ...newProps };
//     });
//   };
//   return (
//     <div className="App">
//       <StudentSelectHeader
//         students={["Bart", "Lisa", "Milhouse"]}
//         selected="Bart"
//         setProps={setProps}
//       />
//       {/* <LOConnection /> */}
//       <LOMetrics
//         data={{
//           sentences: {
//             id: "sentences",
//             value: 33,
//             label: " sentences",
//           },
//           paragraphs: {
//             id: "paragraphs",
//             value: 45,
//             label: " paragraphs",
//           },
//         }}
//         shown={["paragraphs", "sentences"]}
//       />
//       <LOIndicatorBars
//         data={{
//           sentences: {
//             id: "sentences",
//             value: 33,
//             label: " bananas",
//           },
//           paragraphs: {
//             id: "paragraphs",
//             value: 45,
//             label: " paragraphs",
//           },
//         }}
//         shown={["paragraphs", "sentences"]}
//       />

//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Editing <code>src/App.js</code> and save to reload and this changes.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;
