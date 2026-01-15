# Flask Blog

Prosty blog z szablonami Jinja2 i SQLite.

## Uruchomienie

```bash
markpact examples/flask-blog/README.md
```

Blog będzie dostępny pod: http://localhost:5000

## Funkcje

- Lista postów na stronie głównej
- Dodawanie nowych postów
- Widok pojedynczego posta
- Responsywny design (Pico CSS)

---

```text markpact:deps python
flask
```

```python markpact:file path=app.py
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'blog.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

@app.route('/')
def index():
    db = get_db()
    posts = db.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:id>')
def post(id):
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (id,)).fetchone()
    return render_template('post.html', post=post)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        db = get_db()
        db.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
        db.commit()
        return redirect(url_for('index'))
    return render_template('new.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

```html markpact:file path=templates/base.html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Blog{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
</head>
<body>
    <main class="container">
        <nav>
            <ul><li><strong>📝 Markpact Blog</strong></li></ul>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/new">Nowy post</a></li>
            </ul>
        </nav>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

```html markpact:file path=templates/index.html
{% extends "base.html" %}
{% block title %}Blog - Strona główna{% endblock %}
{% block content %}
<h1>Posty</h1>
{% for post in posts %}
<article>
    <header>
        <h2><a href="/post/{{ post.id }}">{{ post.title }}</a></h2>
        <small>{{ post.created_at }}</small>
    </header>
    <p>{{ post.content[:200] }}{% if post.content|length > 200 %}...{% endif %}</p>
</article>
{% else %}
<p>Brak postów. <a href="/new">Dodaj pierwszy!</a></p>
{% endfor %}
{% endblock %}
```

```html markpact:file path=templates/post.html
{% extends "base.html" %}
{% block title %}{{ post.title }}{% endblock %}
{% block content %}
<article>
    <header>
        <h1>{{ post.title }}</h1>
        <small>{{ post.created_at }}</small>
    </header>
    <p>{{ post.content }}</p>
    <footer><a href="/">← Powrót</a></footer>
</article>
{% endblock %}
```

```html markpact:file path=templates/new.html
{% extends "base.html" %}
{% block title %}Nowy post{% endblock %}
{% block content %}
<h1>Nowy post</h1>
<form method="post">
    <label>Tytuł
        <input type="text" name="title" required>
    </label>
    <label>Treść
        <textarea name="content" rows="10" required></textarea>
    </label>
    <button type="submit">Opublikuj</button>
</form>
{% endblock %}
```

```bash markpact:run
python app.py
```
