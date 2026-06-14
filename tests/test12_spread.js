// Spread operator test
let arr1 = [1, 2, 3];
let arr2 = [...arr1, 4, 5];
console.log(arr2.join(", "));
let obj1 = { a: 1, b: 2 };
let obj2 = { ...obj1, c: 3 };
console.log(Object.keys(obj2).join(", "));
