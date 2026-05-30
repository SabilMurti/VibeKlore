/**
 * Math operations module.
 * Provides addition function that supports numeric inputs and convertible string inputs.
 */

/**
 * Adds two values after converting them to numbers.
 * @param {*} a - First value
 * @param {*} b - Second value
 * @returns {number} Sum of a and b
 */
function add(a, b) {
    return Number(a) + Number(b);
}

module.exports = {
    add: add
};
