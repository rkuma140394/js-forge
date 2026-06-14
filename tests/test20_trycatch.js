// try-catch test
let result;
try {
    let x = 10;
    result = x / 0;
    console.log("No error");
} catch (e) {
    console.log("Error caught");
} finally {
    console.log("Finally block");
}
console.log(result);
