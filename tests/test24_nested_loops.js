// Nested loops with break/continue
let result = "";
for (let i = 1; i <= 3; i++) {
    for (let j = 1; j <= 3; j++) {
        if (j === 2) continue;
        result += i + "" + j + " ";
    }
}
console.log(result.trim());
