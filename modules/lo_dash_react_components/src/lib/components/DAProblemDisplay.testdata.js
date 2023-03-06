/* eslint-disable no-magic-numbers */

const SAMPLE_PROBLEMS = [
  {
    title: 'Bouncing Ball',
    description:
    'Determine the maximum height, time to reach maximum height, and total time a ball is in the air when thrown straight up with a given velocity.',
    id: 'ms-bouncing-ball',
    related_scaffolds: ['scaffold-graphs', 'scaffold-parabolas'],
  },
  {
    title: 'Pizza Party',
    description:
    'Calculate the number of pizzas needed and the cost of a pizza party based on the number of guests and their average pizza consumption.',
    id: 'ms-pizza-party',
    related_scaffolds: ['scaffold-rates', 'scaffold-percentages'],
  },
  {
    title: 'Scaling Shapes',
    description:
    'Determine the scale factor, new dimensions, and area of a shape after it is scaled by a given factor.',
    id: 'ms-scaling-shapes',
    related_scaffolds: [
      'scaffold-equations',
      'scaffold-graphs',
      'scaffold-units',
    ],
  },
  {
    title: 'Sports Stats',
    description:
    'Compute and compare statistics such as batting average, on-base percentage, and slugging percentage for different baseball players or teams.',
    id: 'ms-sports-stats',
    related_scaffolds: ['scaffold-rates', 'scaffold-graphs'],
  },
];

// Sample scaffolds for testing purposes
const SAMPLE_SCAFFOLDS = [
  {
    id: 'scaffold-rates',
    title: 'Rates',
    description:
    'A worked example that shows how to calculate rate of change and apply it to real-world problems.',
  },
  {
    id: 'scaffold-parabolas',
    title: 'Parabolas',
    description:
    'A formula sheet that explains the properties and graphs of parabolas, and how to find the equation of a parabola from given information.',
  },
  {
    id: 'scaffold-equations',
    title: 'Equations',
    description:
    'A list of formulas and tips for solving equations, including linear equations, quadratic equations, and systems of equations.',
  },
  {
    id: 'scaffold-units',
    title: 'Units',
    description:
    'A reference sheet that shows common units of measurement for length, weight, time, and temperature, and how to convert between them.',
  },
  {
    id: 'scaffold-graphs',
    title: 'Graphs',
    description:
    'A set of sample graphs that illustrate various types of relationships, including linear, quadratic, and exponential.',
  },
  {
    id: 'scaffold-percentages',
    title: 'Percentages',
    description:
    'A step-by-step guide to calculating percentages, including tips for solving percentage word problems.',
  },
];

/**
 * generateInitials generates a two-letter string that represents a person's
 * initials. The function randomly generates two uppercase letters from the
 * alphabet and concatenates them into a string.
 *
 * @returns {string} A two-letter string representing a person's initials.
 */
function generateInitials() {
  const first = String.fromCharCode(65 + Math.floor(Math.random() * 26));
  const last = String.fromCharCode(65 + Math.floor(Math.random() * 26));
  return first + last;
}

function generateSampleStudents(n, problems, scaffolds, p) {
  const students = [];
  
  for (let i = 0; i < n; i++) {
    const initials = generateInitials();
    const problem = problems[Math.floor(Math.random() * problems.length)].id;
    const scaffold =
          Math.random() < p
          ? scaffolds[Math.floor(Math.random() * scaffolds.length)].id
          : null;
    const id = 'student-' + i;
    students.push({ initials: initials, problem: problem, scaffold: scaffold, id: id });
  }
  
  return students;
}

const SAMPLE_STUDENTS = generateSampleStudents(
  10,
  SAMPLE_PROBLEMS,
  SAMPLE_SCAFFOLDS,
  0.5
);

const testData = {
  students: SAMPLE_STUDENTS,
  problems: SAMPLE_PROBLEMS,
  scaffolds: SAMPLE_SCAFFOLDS
};

export default testData;
