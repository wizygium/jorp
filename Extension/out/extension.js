const vscode = require('vscode');
const cp = require('child_process');

// Minimal placeholder for VS Code extension entry point
function activate(context) {
    let disposable = vscode.commands.registerCommand('pcsp.checkSyntax', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor.');
            return;
        }
        const filePath = editor.document.fileName;
        editor.document.save().then(() => {
            const patEnv = 'C:\\Program Files (x86)\\Process Analysis Toolkit\\Process Analysis Toolkit 3.5.1\\PATEnv.bat';
            const patExe = 'C:\\Program Files (x86)\\Process Analysis Toolkit\\Process Analysis Toolkit 3.5.1\\PAT3.Console.exe';
            const patDir = require('path').dirname(patExe);
            const dummyOut = filePath + '.patout';
            const patCmd = `"${patExe}" -pcsp "${filePath}" "${dummyOut}"`;
            // Launch PATEnv.bat and then run the PAT command
            cp.exec(`cmd.exe /c "\"${patEnv}\" && ${patCmd}"`, { cwd: patDir }, (err, stdout, stderr) => {
                const output = vscode.window.createOutputChannel('PAT');
                output.clear();
                if (stdout) output.appendLine(stdout);
                if (stderr) output.appendLine(stderr);
                output.show();
                if (err) {
                    vscode.window.showErrorMessage(`PAT error: ${stderr || err.message}`);
                } else {
                    vscode.window.showInformationMessage('PAT syntax check complete.');
                }
            });
        });
    });
    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
