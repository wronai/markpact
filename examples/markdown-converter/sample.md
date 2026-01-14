# Sample Project (Regular Markdown)

This is a regular Markdown file WITHOUT any `markpact:*` tags.
Markpact can automatically convert it to markpact format.

## Installation

Install the required dependencies:

```
fastapi
uvicorn
pydantic
```

## Code

Here's the main application:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Sample API")

class Item(BaseModel):
    name: str
    price: float

items: list[Item] = []

@app.get("/items")
def list_items():
    return items

@app.post("/items")
def add_item(item: Item):
    items.append(item)
    return item

@app.get("/health")
def health():
    return {"status": "ok"}
```

## Running

Start the server:

```bash
uvicorn app:app --reload --port 8000
```

## Testing

You can test the API with curl:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/items -H "Content-Type: application/json" -d '{"name": "Test", "price": 9.99}'
curl http://localhost:8000/items
```
