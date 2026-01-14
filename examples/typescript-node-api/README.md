# TypeScript Node API Example

Minimalne REST API w TypeScript (Node) uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/typescript-node-api/README.md
```

---

```markpact:file json path=package.json
{
  "name": "markpact-ts-node-api",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts"
  },
  "dependencies": {
    "express": "^4.21.2",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/cors": "^2.8.17",
    "@types/node": "^22.13.1",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2"
  }
}
```

```markpact:file ts path=tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

```markpact:file ts path=src/index.ts
import express from 'express'
import cors from 'cors'

interface Health {
  status: string
}

interface EchoRequest {
  message: string
}

interface EchoResponse {
  message: string
}

const app = express()
const port = Number(process.env.MARKPACT_PORT) || 4000

app.use(cors())
app.use(express.json())

app.get('/health', (req, res): void => {
  res.json({ status: 'ok' } satisfies Health)
})

app.post('/echo', (req, res): void => {
  const { message } = req.body as EchoRequest
  if (typeof message !== 'string') {
    res.status(400).json({ error: 'message must be a string' })
    return
  }
  res.json({ message } satisfies EchoResponse)
})

app.listen(port, '0.0.0.0', () => {
  console.log(`Listening on http://0.0.0.0:${port}`)
})
```

```markpact:run shell
npm install
npm run build && npm start
```

```markpact:test http
GET /health EXPECT 200
POST /echo BODY {"message":"hello"} EXPECT 200
```
