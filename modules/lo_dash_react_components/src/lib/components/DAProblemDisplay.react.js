import React, { useEffect, useLayoutEffect, useRef } from 'react';

import PropTypes from 'prop-types';
import { PieChart, Pie, Cell, Label } from 'recharts';
import { Arrow, initArrows, updateArrowPositions, stagger, djb2 } from './helperlib';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const studentPropType = {
  initials: PropTypes.string.isRequired,
  problem: PropTypes.string.isRequired,
  scaffold: PropTypes.string,
  id: PropTypes.string.isRequired,
};

const studentsPropType = PropTypes.arrayOf(PropTypes.shape(studentPropType));

const problemPropType = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  related_scaffolds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
};

const problemsPropType = PropTypes.arrayOf(PropTypes.shape(problemPropType));

const scaffoldPropType = {
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
};

const scaffoldsPropType = PropTypes.arrayOf(PropTypes.shape(scaffoldPropType));

function addCountAndIndex(data, field) {
  const counts = {};
  let indexedData = data.map((obj) => {
    const fieldValue = obj[field];
    if (fieldValue in counts) {
      counts[fieldValue]++;
    } else {
      counts[fieldValue] = 0;
    }
    return { ...obj, index: counts[fieldValue] };
  });
  indexedData = indexedData.map((obj) => {
    const fieldValue = obj[field];
    return { ...obj, count: counts[fieldValue] + 1 };
  });
  return indexedData;
}

function Problem({ id, title, description }) {
  /* Dummy data. We'll bring in real data later. */
  const students = [{ initials: 'am' }, { initials: 'pm' }, { initials: 'cj' }];
  const data = [
    { name: 'Green', value: 10 },
    { name: 'Yellow', value: 5 },
    { name: 'Red', value: 3 },
    { name: 'Grey', value: 2 },
  ];

  const totalStudents = students.length;

  return (
    <div id={'problem-' + id} className="card problem">
      <div style={{ display: 'flex' }}>
        <div style={{ flex: 1, marginRight: '10px' }}>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <div style={{ width: '80px', height: '80px' }}>
          <PieChart width={80} height={80}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={20}
              outerRadius={40}
              isanimation={false}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
              <Label value={`${totalStudents}`} position="center" />
            </Pie>
          </PieChart>
        </div>
      </div>
      <div className="initials-box" id={'initials-problem-' + id}></div>
    </div>
  );
}

Problem.propTypes = problemPropType;

function Scaffold({ id, title, description }) {
  return (
    <div id={'scaffold-' + id} className="card scaffold">
      <div className="target-box" id={'initials-target-' + id}></div>
      <div className="scaffold-content">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

Scaffold.propTypes = scaffoldPropType;

function Students({ students }) {
  useEffect(() => {
    function moveStudents() {
      const index_students = addCountAndIndex(students, 'problem');
      index_students.forEach((student) => {
        const targetBox = document.querySelector(
          `#${`initials-problem-${student.problem}`}`
        );
        // const sourceBox = document.querySelector('#student-container');
        // const sourceRect = sourceBox.getBoundingClientRect();
        const studentCircle = document.querySelector(`#${student.id}`);

        const targetRect = targetBox.getBoundingClientRect();
        const studentRect = studentCircle.getBoundingClientRect();
        const top =
          targetRect.top - studentRect.height / 2 + targetRect.height / 2;
        const left =
          targetRect.left -
          studentRect.width / 2 +
          targetRect.width * stagger(student.index, student.count);
        studentCircle.style.position = 'absolute';
        studentCircle.style.top = `${top}px`;
        studentCircle.style.left = `${left}px`;
      });
    }
    moveStudents();
    window.addEventListener('resize', moveStudents);
    return () => {
      window.removeEventListener('resize', moveStudents);
    };
  }, [students]);

  return (
    <div className="students" id="student-container">
      {students.map((student) => (
        <div
          className="student-initials"
          data-target={'initials-problem-' + student.problem}
          id={student.id}
          key={student.id}
        >
          {student.initials}
        </div>
      ))}
    </div>
  );
}

Students.propTypes = {
  students: studentsPropType.isRequired
};

function Connectors() {
  return <div className="connectors" />;
}

function Arrows({ students }) {
  useLayoutEffect(() => {
    updateArrowPositions();
  }, []);

  const arrows = [];

  students.forEach((student) => {
    const { id, scaffold } = student;
    if (scaffold) {
      const scaffoldId = 'initials-target-' + scaffold;
      arrows.push(
        <Arrow
          key={"arrow_"+id}
          source={id}
          target={scaffoldId}
        />
      );
    }
  });

  return <div className="arrow-wrapper" id="arrow-wrapper">{arrows}</div>;
}

Arrows.propTypes = {
  students: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    initials: PropTypes.string.isRequired,
    problem: PropTypes.string.isRequired
  })).isRequired
};

Arrows.propTypes = {
  students: studentsPropType.isRequired
};

function BackgroundCanvas({ problems }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    function renderCanvas() {
      context.clearRect(0, 0, canvas.width, canvas.height);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      context.translate(-rect.left, -rect.top);

      // Now you can draw on the canvas using ClientRect coordinates
      context.lineWidth = 6;
      for (const problem of problems) {
        for (const scaffold of problem.related_scaffolds) {
          context.beginPath();
          const problem_element = document.getElementById(
            'problem-' + problem.id
          );
          const scaffold_element = document.getElementById(
            'scaffold-' + scaffold
          );
          const problem_rect = problem_element.getBoundingClientRect();
          const scaffold_rect = scaffold_element.getBoundingClientRect();

          const startX = problem_rect.right;
          const startY = problem_rect.top + problem_rect.height / 2;
          const endX = scaffold_rect.left;
          const endY = scaffold_rect.top + scaffold_rect.height / 2;

          const control1X = startX + (endX - startX) / 2;
          const control1Y = startY;
          const control2X = control1X;
          const control2Y = endY;

          context.moveTo(startX, startY);
          context.bezierCurveTo(
            control1X,
            control1Y,
            control2X,
            control2Y,
            endX,
            endY
          );
          const gradient = context.createLinearGradient(startX, 0, endX, 0);
          const degreesInCircle = 360;
          const problem_hash = djb2(problem.id) % degreesInCircle;
          const scaffold_hash = djb2(scaffold) % degreesInCircle;
          gradient.addColorStop(0, `hsl(${problem_hash}, 56%, 80%)`);
          gradient.addColorStop(1, `hsl(${scaffold_hash}, 56%, 80%)`);
          context.strokeStyle = gradient;
          context.stroke();
        }
      }
    }
    renderCanvas();
    window.addEventListener('resize', renderCanvas);
    return () => {
      window.removeEventListener('resize', renderCanvas);
    };
  }, []);

  return <canvas ref={canvasRef} className="background-canvas" />;
}

BackgroundCanvas.propTypes ={
  problems: problemsPropType.isRequired
};


function Container({ problems, scaffolds }) {
  return (
    <div className="container">
      <div className="problem-container">
        {problems.map((problem, index) => (
          <Problem key={index} {...problem} />
        ))}
      </div>
      <Connectors />
      <div className="scaffold-container">
        {scaffolds.map((scaffold, index) => (
          <Scaffold key={index} {...scaffold} />
        ))}
      </div>
    </div>
  );
}

Container.propTypes ={
  problems: problemsPropType.isRequired,
  scaffolds: scaffoldsPropType.isRequired
};

/* The DAProblemDisplay component is responsible for displaying
 * information about students, problems, and scaffolds. It takes in an
 * array of student objects, each containing their initials, the
 * problem they are working on, the scaffold they are using (if any),
 * and their unique ID.
 *
 * It renders which scaffolds associate with which problems, and which
 * scaffolds or problems students are currently using.
 */
class DAProblemDisplay extends React.Component {
  render() {
    const { students, problems, scaffolds } = this.props;
    return (
      <div className="App" id="problem-page-wrapper">
        <Arrows students={students} />
        <Container problems={problems} scaffolds={scaffolds} />
        <Students students={students} />
        <BackgroundCanvas problems={problems} />
      </div>
    );
  }
}

DAProblemDisplay.propTypes = {
  /* students (array): An array of objects containing information about each student:
   *    - initials (string): The student's initials.
   *    - problem (string): The ID of the problem the student is working on.
   *    - scaffold (string): The ID of the scaffold the student is using (if any).
   *    - id (string): The unique ID of the student.
   */
  students: PropTypes.arrayOf(
    PropTypes.shape({
      initials: PropTypes.string.isRequired,
      problem: PropTypes.string.isRequired,
      scaffold: PropTypes.string,
      id: PropTypes.string.isRequired,
    })
  ).isRequired,
  /* problems (array): An array of objects containing information about each problem:
   *    - title (string): The title of the problem.
   *    - description (string): A description of the problem.
   *    - id (string): The unique ID of the problem.
   *    - related_scaffolds (array): An array of strings representing the IDs of scaffolds related to the problem.
   */
  problems: PropTypes.arrayOf(PropTypes.shape({
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    id: PropTypes.string.isRequired,
    related_scaffolds: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  })).isRequired,
  /* scaffolds (array): An array of objects containing information about each scaffold:
   *    - id (string): The unique ID of the scaffold.
   *    - title (string): The title of the scaffold.
   *    - description (string): A description of the scaffold.
   *    - content (string): The content of the scaffold.
   */
  scaffolds: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
  })).isRequired,};

initArrows();

export default DAProblemDisplay;
