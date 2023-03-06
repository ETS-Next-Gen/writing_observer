import React, { Component, useState } from "react";
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import logo from "./logo.svg";
import "./App.css";

import "./css/styles.css";
import "bootstrap/dist/css/bootstrap.min.css";

import {
  LOConnection,
  LOMetrics,
  LOIndicatorBars,
  StudentSelectHeader,
} from "./lib";

const components = {};

const importAll = (r) => {
  r.keys().forEach((key) => {
    const componentName = key.replace('./', '').replace('.react.js', '');
    components[componentName] = {
      component: r(key).default,
      testdata: testData(componentName)
    };
  });
};

function testData(component_name) {
  let testData = {};
  try {
    testData = require(`./lib/components/${component_name}.testdata.js`).default;
    console.log("Loaded test data for " + component_name);
  } catch (error) {
    console.log("No test data for " + component_name);
  }
  return testData;
}

importAll(require.context('./lib/components', true, /\.react.js$/));

function ComponentList(props) {
  return (
    <div>
      <hr/>
      <h1>Component list</h1>
      <ul>
        {Object.entries(components).map(([name, component]) => (
          <li key={"li_"+name}> <a href={"/components/"+name}  key={"a_"+name}>{name}</a> </li>
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
