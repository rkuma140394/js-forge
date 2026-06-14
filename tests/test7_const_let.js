// const and let scoping
let x = 10;
const y = 20;
if (true) {
    let x = 30;
    console.log(x);
}
console.log(x);
console.log(y);
