// Callbacks and closures
function makeMultiplier(factor) {
    return function(num) {
        return num * factor;
    };
}
let triple = makeMultiplier(3);
console.log(triple(4));
console.log(triple(5));

function forEach(arr, callback) {
    for (let i = 0; i < arr.length; i++) {
        callback(arr[i], i);
    }
}
let sum = 0;
forEach([1, 2, 3], function(val, idx) {
    sum += val;
});
console.log(sum);
