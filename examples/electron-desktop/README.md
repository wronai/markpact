# Electron Desktop App

Aplikacja desktopowa (Windows/macOS/Linux) – notatnik Markdown.

## Uruchomienie

```bash
markpact examples/electron-desktop/README.md
```

> **Uwaga:** Wymaga Node.js. Ten przykład demonstruje użycie markpact z Node.js (planowana obsługa `markpact:deps node`).

## Funkcje

- Edytor Markdown z podglądem na żywo
- Zapis/odczyt plików
- Eksport do HTML
- Dark mode

---

```text markpact:deps python
# Python bootstrap tylko tworzy pliki
# Uruchomienie wymaga: npm install && npm start
```

```json markpact:file path=package.json
{
  "name": "markdown-notes",
  "version": "1.0.0",
  "description": "Markdown Notes - Desktop App",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder"
  },
  "dependencies": {
    "electron": "^28.0.0",
    "marked": "^11.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0"
  }
}
```

```javascript markpact:file path=main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// File operations
ipcMain.handle('open-file', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [{ name: 'Markdown', extensions: ['md', 'markdown'] }]
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
        const content = fs.readFileSync(result.filePaths[0], 'utf-8');
        return { path: result.filePaths[0], content };
    }
    return null;
});

ipcMain.handle('save-file', async (event, { path: filePath, content }) => {
    if (!filePath) {
        const result = await dialog.showSaveDialog(mainWindow, {
            filters: [{ name: 'Markdown', extensions: ['md'] }]
        });
        if (result.canceled) return null;
        filePath = result.filePath;
    }
    fs.writeFileSync(filePath, content);
    return filePath;
});
```

```html markpact:file path=index.html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Markdown Notes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e1e;
            color: #d4d4d4;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .toolbar {
            background: #252526;
            padding: 10px;
            display: flex;
            gap: 10px;
            border-bottom: 1px solid #3c3c3c;
        }
        
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        button:hover { background: #1177bb; }
        
        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        .editor, .preview {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .editor {
            background: #1e1e1e;
            border-right: 1px solid #3c3c3c;
        }
        
        #markdown-input {
            width: 100%;
            height: 100%;
            background: transparent;
            border: none;
            color: #d4d4d4;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            resize: none;
            outline: none;
        }
        
        .preview {
            background: #252526;
        }
        
        #preview-content {
            line-height: 1.8;
        }
        
        #preview-content h1, #preview-content h2, #preview-content h3 {
            color: #569cd6;
            margin: 20px 0 10px 0;
        }
        
        #preview-content code {
            background: #1e1e1e;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Fira Code', monospace;
        }
        
        #preview-content pre {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }
        
        #preview-content a { color: #4ec9b0; }
        #preview-content blockquote {
            border-left: 4px solid #569cd6;
            padding-left: 15px;
            color: #808080;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <button onclick="openFile()">📂 Open</button>
        <button onclick="saveFile()">💾 Save</button>
        <button onclick="exportHtml()">📤 Export HTML</button>
        <span id="filename" style="margin-left: auto; color: #808080;"></span>
    </div>
    
    <div class="container">
        <div class="editor">
            <textarea id="markdown-input" placeholder="Write your Markdown here..."></textarea>
        </div>
        <div class="preview">
            <div id="preview-content"></div>
        </div>
    </div>
    
    <script>
        const { ipcRenderer } = require('electron');
        const { marked } = require('marked');
        
        const input = document.getElementById('markdown-input');
        const preview = document.getElementById('preview-content');
        const filenameEl = document.getElementById('filename');
        
        let currentPath = null;
        
        // Live preview
        input.addEventListener('input', () => {
            preview.innerHTML = marked(input.value);
        });
        
        // Initial content
        input.value = `# Welcome to Markdown Notes

Start writing your notes here!

## Features

- **Live preview** as you type
- Save and open files
- Export to HTML

\`\`\`javascript
console.log('Hello, World!');
\`\`\`

> This is a blockquote

Enjoy writing! ✨`;
        preview.innerHTML = marked(input.value);
        
        async function openFile() {
            const result = await ipcRenderer.invoke('open-file');
            if (result) {
                input.value = result.content;
                preview.innerHTML = marked(result.content);
                currentPath = result.path;
                filenameEl.textContent = currentPath;
            }
        }
        
        async function saveFile() {
            const path = await ipcRenderer.invoke('save-file', {
                path: currentPath,
                content: input.value
            });
            if (path) {
                currentPath = path;
                filenameEl.textContent = path;
            }
        }
        
        function exportHtml() {
            const html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Export</title>
<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;}</style>
</head><body>${marked(input.value)}</body></html>`;
            
            const blob = new Blob([html], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'export.html';
            a.click();
        }
    </script>
</body>
</html>
```

```bash markpact:run
echo "Electron app created. To run:"
echo "  cd sandbox && npm install && npm start"
echo ""
echo "Files created:"
ls -la
```
