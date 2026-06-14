// Array slice and splice
let arr = [1, 2, 3, 4, 5];
let sliced = arr.slice(1, 4);
console.log(sliced.join(", "));
console.log(arr.join(", "));
let removed = arr.splice(2, 2);
console.log(removed.join(", "));
console.log(arr.join(", "));
