// Array methods: map, filter, reduce
let nums = [1, 2, 3, 4, 5];
let doubled = nums.map(n => n * 2);
console.log(doubled.join(", "));
let evens = nums.filter(n => n % 2 === 0);
console.log(evens.join(", "));
let sum = nums.reduce((acc, n) => acc + n, 0);
console.log(sum);
let firstEven = nums.find(n => n % 2 === 0);
console.log(firstEven);
console.log(nums.some(n => n > 4));
console.log(nums.every(n => n > 0));
