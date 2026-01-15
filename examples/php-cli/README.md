# PHP CLI Example

Minimalne CLI w PHP uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/php-cli/README.md
```

---

```php markpact:file path=src/Greeter.php
<?php

class Greeter
{
    public function greet(string $name = 'World'): string
    {
        return "Hello, {$name}!";
    }

    public function sum(int $a, int $b): int
    {
        return $a + $b;
    }
}
```

```php markpact:file path=bin/cli.php
#!/usr/bin/env php
<?php

require_once __DIR__ . '/../src/Greeter.php';

$greeter = new Greeter();

$opts = getopt('n:a::b::h', ['name:', 'add::', 'help']);
if (isset($opts['h']) || isset($opts['help'])) {
    echo "Usage: php cli.php --name <name> | --add <a> <b>\n";
    exit(0);
}

if (isset($opts['n']) || isset($opts['name'])) {
    $name = $opts['n'] ?? $opts['name'];
    echo $greeter->greet($name) . PHP_EOL;
} elseif (isset($opts['a']) || isset($opts['add'])) {
    $a = $opts['a'] ?? $opts['add'][0] ?? 0;
    $b = $opts['b'] ?? $opts['add'][1] ?? 0;
    echo "{$a} + {$b} = " . $greeter->sum((int)$a, (int)$b) . PHP_EOL;
} else {
    echo $greeter->greet() . PHP_EOL;
}
```

```bash markpact:run
php bin/cli.php --name ${MARKPACT_NAME:-World}
```

```bash markpact:test shell
php bin/cli.php --name Markpact
php bin/cli.php --add 3 7
```
