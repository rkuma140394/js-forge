// Objects
const students = [
    { id: 1, name: "Rohit", marks: [85, 90, 88] },
    { id: 2, name: "Aman", marks: [70, 75, 80] },
    { id: 3, name: "Priya", marks: [95, 92, 98] }
];

// Arrow Function
const calculateAverage = (marks) => {
    return marks.reduce((sum, mark) => sum + mark, 0) / marks.length;
};

// map + spread operator
const report = students.map(student => ({
    ...student,
    average: calculateAverage(student.marks)
}));

// filter
const toppers = report.filter(student => student.average >= 90);

// sort
toppers.sort((a, b) => b.average - a.average);

// Closure
function createCounter(start) {
    let count = start;

    return function () {
        count++;
        return count;
    };
}

const counter = createCounter(100);

// Output
console.log("=== Student Report ===");

report.forEach(student => {
    console.log(
        `${student.name}: ${student.average.toFixed(2)}`
    );
});

console.log("=== Toppers ===");

toppers.forEach(student => {
    console.log(student.name);
});

console.log("Counter:");
console.log(counter());
console.log(counter());

// Destructuring
const [firstStudent] = students;
const { name } = firstStudent;

console.log("First Student:", name);

// String Methods
const text = "  JavaScript Interpreter  ";

console.log(text.trim().toUpperCase());

// Array Methods
const nums = [1, 2, 3, 4, 5];

const result = nums
    .filter(n => n % 2 === 1)
    .map(n => n * n)
    .reduce((a, b) => a + b, 0);

console.log("Result:", result);