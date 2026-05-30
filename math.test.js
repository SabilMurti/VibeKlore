const assert = require('assert');
const math = require('./math.js');

console.log("Running unit tests for math.js...");

try {
    // 1. Adding two positive numbers
    assert.strictEqual(math.add(2, 3), 5, "Adding two positive numbers failed");
    console.log("✓ PASS: Adding two positive numbers (2 + 3 = 5)");

    // 2. Adding two negative numbers
    assert.strictEqual(math.add(-5, -10), -15, "Adding two negative numbers failed");
    console.log("✓ PASS: Adding two negative numbers (-5 + -10 = -15)");

    // 3. Adding a positive and a negative number
    assert.strictEqual(math.add(7, -3), 4, "Adding positive and negative numbers failed");
    console.log("✓ PASS: Adding positive and negative numbers (7 + -3 = 4)");

    // 4. Adding non-numeric inputs (strings that can be converted to numbers)
    assert.strictEqual(math.add("10", "20"), 30, "Adding numeric strings failed");
    assert.strictEqual(math.add(1.5, "2.5"), 4.0, "Adding float and string float failed");
    console.log("✓ PASS: Adding non-numeric inputs that can be converted to numbers");

    // 5. Extra edge cases: null and undefined
    // Number(null) is 0
    assert.strictEqual(math.add(5, null), 5, "Adding with null failed");
    // Number(undefined) is NaN, so NaN + number is NaN
    assert.isNaN = function(value, message) {
        if (!isNaN(value)) {
            throw new assert.AssertionError({
                message: message || "Expected value to be NaN",
                actual: value,
                expected: NaN
            });
        }
    };
    assert.isNaN(math.add(5, undefined), "Adding with undefined should result in NaN");
    console.log("✓ PASS: Edge cases (null, undefined)");

    console.log("\nAll unit tests passed successfully!");
    process.exit(0);
} catch (error) {
    console.error("\nTEST FAILED:");
    console.error(error.message);
    process.exit(1);
}
