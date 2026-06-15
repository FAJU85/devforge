import React, { useState } from 'react';

interface CodeDiffViewerProps {
  originalCode: string;
  modifiedCode: string;
  diff: string;
  filePath: string;
  instruction: string;
  onApprove: () => void;
  onReject?: () => void;
  isCreatingPR?: boolean;
}

type ViewMode = 'split' | 'diff';

export const CodeDiffViewer: React.FC<CodeDiffViewerProps> = ({
  originalCode,
  modifiedCode,
  diff,
  filePath,
  instruction,
  onApprove,
  onReject,
  isCreatingPR = false,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [copiedOriginal, setCopiedOriginal] = useState(false);
  const [copiedModified, setCopiedModified] = useState(false);

  const handleCopy = (code: string, isMod: boolean) => {
    navigator.clipboard.writeText(code);
    if (isMod) {
      setCopiedModified(true);
      setTimeout(() => setCopiedModified(false), 2000);
    } else {
      setCopiedOriginal(true);
      setTimeout(() => setCopiedOriginal(false), 2000);
    }
  };

  const CodeBlock: React.FC<{ code: string; label: string; isCopied: boolean }> = ({
    code,
    label,
    isCopied,
  }) => (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <h3 className="font-semibold text-sm text-gray-700">{label}</h3>
        <button
          onClick={() => handleCopy(code, label.includes('Modified'))}
          className="p-1 hover:bg-gray-200 rounded transition flex items-center gap-1 text-xs"
          title="Copy to clipboard"
        >
          {isCopied ? '✓ Copied!' : '📋 Copy'}
        </button>
      </div>
      <pre className="flex-1 overflow-auto p-4 bg-gray-50 text-xs font-mono text-gray-800">
        <code>{code}</code>
      </pre>
    </div>
  );

  return (
    <div className="w-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Code Modification Result</h2>
            <p className="text-sm text-gray-600 mt-1">File: <code className="bg-gray-100 px-2 py-1 rounded">{filePath}</code></p>
          </div>
        </div>
        <p className="text-sm text-gray-700">
          <strong>Instruction:</strong> {instruction}
        </p>
      </div>

      {/* View Mode Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50 px-6">
        <button
          onClick={() => setViewMode('split')}
          className={`px-4 py-2 font-medium text-sm transition ${
            viewMode === 'split'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Side-by-Side
        </button>
        <button
          onClick={() => setViewMode('diff')}
          className={`px-4 py-2 font-medium text-sm transition ${
            viewMode === 'diff'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Unified Diff
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {viewMode === 'split' ? (
          <div className="grid grid-cols-2 gap-4 h-96">
            <CodeBlock
              code={originalCode}
              label="Original"
              isCopied={copiedOriginal}
            />
            <CodeBlock
              code={modifiedCode}
              label="Modified"
              isCopied={copiedModified}
            />
          </div>
        ) : (
          <div className="bg-gray-50 rounded border border-gray-200 overflow-auto max-h-96">
            <pre className="p-4 text-xs font-mono text-gray-800">
              <code>{diff || 'No differences'}</code>
            </pre>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
        <button
          onClick={onApprove}
          disabled={isCreatingPR}
          className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
        >
          {isCreatingPR ? (
            <>
              <span className="animate-spin">⏳</span>
              Creating PR...
            </>
          ) : (
            '✓ Create GitHub PR'
          )}
        </button>
        <button
          onClick={onReject}
          disabled={isCreatingPR || !onReject}
          className="flex-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-400 text-gray-900 font-medium py-2 px-4 rounded-lg transition"
        >
          Reject Changes
        </button>
      </div>

      {/* Info */}
      <div className="px-6 py-3 bg-blue-50 border-t border-blue-200 text-sm text-blue-800 flex items-start gap-2">
        <span>ℹ️</span>
        <span>
          Review the changes above. Click "Create GitHub PR" to submit them as a pull request to your repository.
        </span>
      </div>
    </div>
  );
};
