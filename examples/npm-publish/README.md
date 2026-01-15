# npm Publish Example

Przykład publikacji paczki JavaScript/Node.js do npm bezpośrednio z README.

## Użycie

```bash
# Podgląd bez publikacji
markpact examples/npm-publish/README.md --publish --dry-run

# Publikacja do npm
markpact examples/npm-publish/README.md --publish

# Publikacja z bump wersji
markpact examples/npm-publish/README.md --publish --bump minor

# Publikacja do GitHub Packages
markpact examples/npm-publish/README.md --publish --registry github
```

## Konfiguracja

Zaloguj się do npm:

```bash
npm login
```

Dla GitHub Packages, dodaj do `~/.npmrc`:

```
//npm.pkg.github.com/:_authToken=ghp_xxxx
```

---

```toml markpact:publish
registry = npm
name = @yourscope/example-package
version = 0.1.0
description = Example npm package published with markpact
author = Your Name
license = MIT
keywords = example, markpact, node
repository = https://github.com/your/repo
```

```javascript markpact:file path=index.js
/**
 * Example npm package published with markpact
 * @module @yourscope/example-package
 */

/**
 * Say hello to someone
 * @param {string} name - Name to greet
 * @returns {string} Greeting message
 */
function hello(name = "World") {
    return `Hello, ${name}!`;
}

/**
 * Add two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 */
function add(a, b) {
    return a + b;
}

/**
 * Multiply two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Product of a and b
 */
function multiply(a, b) {
    return a * b;
}

module.exports = {
    hello,
    add,
    multiply,
};
```

```javascript markpact:file path=cli.js
#!/usr/bin/env node
/**
 * CLI for example package
 */

const { hello, add } = require('./index');

const args = process.argv.slice(2);

if (args[0] === '--add' && args[1] && args[2]) {
    const result = add(parseInt(args[1]), parseInt(args[2]));
    console.log(`${args[1]} + ${args[2]} = ${result}`);
} else if (args[0] === '--name') {
    console.log(hello(args[1] || 'World'));
} else {
    console.log(hello());
}
```

```json markpact:file path=package.json
{
  "name": "@yourscope/example-package",
  "version": "0.1.0",
  "description": "Example npm package published with markpact",
  "main": "index.js",
  "bin": {
    "example-cli": "./cli.js"
  },
  "scripts": {
    "test": "node -e \"const m = require('./index'); console.log(m.hello('Test')); console.log(m.add(2, 3));\""
  },
  "keywords": ["example", "markpact", "node"],
  "author": "Your Name",
  "license": "MIT"
}
```
