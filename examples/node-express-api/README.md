# Node.js Express API Example

Minimalne REST API w Node.js + Express uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/node-express-api/README.md
```

---

```json markpact:file path=package.json
{
  "name": "markpact-express-example",
  "version": "0.1.0",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
```

```javascript markpact:file path=server.js
import express from "express";

const app = express();
app.use(express.json());

const port = process.env.MARKPACT_PORT || 3000;

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.post("/echo", (req, res) => {
  res.json({ message: req.body?.message ?? null });
});

app.listen(port, "0.0.0.0", () => {
  console.log(`Listening on http://0.0.0.0:${port}`);
});
```

```bash markpact:run
npm install
MARKPACT_PORT=${MARKPACT_PORT:-3000} npm start
```

```text markpact:test http
GET /health EXPECT 200
POST /echo BODY {"message":"hello"} EXPECT 200
```
