// Object manipulation
let person = { name: "Alice", age: 25 };
console.log(person.name);
console.log(person.age);
person.age = 26;
console.log(person.age);
let keys = Object.keys(person);
console.log(keys.join(", "));
let values = Object.values(person);
console.log(values.join(", "));
