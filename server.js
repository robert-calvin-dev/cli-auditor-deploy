const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;

app.use(express.static('public'));
app.use(express.json());

app.post('/run-audit', (req, res) => {
  const { url } = req.body;

  if (!/^https?:\/\/[^ "]+$/.test(url)) {
    return res.status(400).send('❌ Invalid URL format.');
  }

  const cliPath = path.join(__dirname, 'seo_auditor_tool');
  const cliFile = path.join(cliPath, 'seo_auditor', 'cli.py');
  const outputDir = path.join(cliPath, 'reports');

  // Use your venv python path here
  const python = path.join(__dirname, 'seo_auditor_tool', 'venv', 'bin', 'python3');

  const cmd = `PYTHONPATH="${cliPath}" ${python} "${cliFile}" "${url}" --output-dir "${outputDir}"`;

  console.log("▶️ Running command:", cmd);

  exec(cmd, (err, stdout, stderr) => {
    console.log('📤 STDOUT:\n', stdout);
    console.log('📛 STDERR:\n', stderr);

    if (err) {
      console.error('❌ CLI failed:', err);
      return res.status(500).send(`❌ CLI execution failed:\n${stderr || stdout || err.message}`);
    }

    const reportFiles = fs.readdirSync(outputDir).filter(f => f.endsWith('.csv'));
    if (!reportFiles.length) {
      console.error("❌ No CSV report found in:", outputDir);
      return res.status(500).send("❌ No CSV report was generated.");
    }

    const mostRecent = reportFiles
      .map(f => ({
        file: f,
        time: fs.statSync(path.join(outputDir, f)).mtime.getTime()
      }))
      .sort((a, b) => b.time - a.time)[0].file;

    console.log("✅ Returning CSV file:", mostRecent);
    res.json({ file: mostRecent });
  });
});

app.get('/download/:file', (req, res) => {
  const filePath = path.join(__dirname, 'seo_auditor_tool', 'reports', req.params.file);
  if (!fs.existsSync(filePath)) return res.status(404).send('❌ File not found.');
  res.download(filePath);
});

app.listen(PORT, () => {
  console.log(`🚀 CLI Sandbox running at http://localhost:${PORT}`);
});
