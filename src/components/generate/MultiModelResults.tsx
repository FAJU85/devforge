import React, { useState } from 'react';

interface ModelResult {
  model: string;
  originalCode: string;
  modifiedCode: string;
  diff: string;
  tokensUsed?: number;
  error?: string;
}

interface MultiModelResultsProps {
  results: ModelResult[];
  instruction: string;
  filePath: string;
  onSelectModel: (model: string, modifiedCode: string) => void;
  isCreatingPR?: boolean;
}

export const MultiModelResults: React.FC<MultiModelResultsProps> = ({
  results,
  instruction,
  filePath,
  onSelectModel,
  isCreatingPR = false,
}) => {
  const [selectedModel, setSelectedModel] = useState<string | null>(
    results.find(r => !r.error)?.model || null
  );
  const [viewMode, setViewMode] = useState<'split' | 'diff'>('split');

  const selectedResult = results.find(r => r.model === selectedModel);
  const successResults = results.filter(r => !r.error);
  const failedResults = results.filter(r => r.error);

  const CodeBlock: React.FC<{ code: string; label: string }> = ({
    code,
    label,
  }) => {
    const [copied, setCopied] = useState(false);

    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
          <h3 className="font-semibold text-sm text-gray-700">{label}</h3>
          <button
            onClick={() => {
              navigator.clipboard.writeText(code);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="p-1 hover:bg-gray-200 rounded transition flex items-center gap-1 text-xs"
            title="Copy to clipboard"
          >
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>
        <pre className="flex-1 overflow-auto p-4 bg-gray-50 text-xs font-mono text-gray-800">
          <code>{code}</code>
        </pre>
      </div>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-900 mb-2">Multi-Model Results</h2>
        <p className="text-sm text-gray-600 mb-1">File: <code className="bg-gray-100 px-2 py-1 rounded">{filePath}</code></p>
        <p className="text-sm text-gray-700">
          <strong>Instruction:</strong> {instruction}
        </p>
      </div>

      {/* Model Selection Grid */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">
          Results from {successResults.length} Model{successResults.length !== 1 ? 's' : ''}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {successResults.map(result => (
            <button
              key={result.model}
              onClick={() => setSelectedModel(result.model)}
              className={`p-3 rounded-lg border-2 transition text-left ${
                selectedModel === result.model
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="font-medium text-sm text-gray-900">{result.model}</div>
              {result.tokensUsed && (
                <div className="text-xs text-gray-500 mt-1">
                  {result.tokensUsed} tokens
                </div>
              )}
              {selectedModel === result.model && (
                <div className="text-blue-600 font-bold mt-1">✓ Selected</div>
              )}
            </button>
          ))}
        </div>

        {failedResults.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <h4 className="text-sm font-semibold text-red-900 mb-2">
              Failed Models ({failedResults.length})
            </h4>
            {failedResults.map(result => (
              <div key={result.model} className="text-sm text-red-700 mb-1">
                <strong>{result.model}:</strong> {result.error}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Results Comparison */}
      {selectedResult && !selectedResult.error && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
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
                  code={selectedResult.originalCode}
                  label="Original"
                />
                <CodeBlock
                  code={selectedResult.modifiedCode}
                  label="Modified"
                />
              </div>
            ) : (
              <div className="bg-gray-50 rounded border border-gray-200 overflow-auto max-h-96">
                <pre className="p-4 text-xs font-mono text-gray-800">
                  <code>{selectedResult.diff || 'No differences'}</code>
                </pre>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
            <button
              onClick={() => onSelectModel(selectedResult.model, selectedResult.modifiedCode)}
              disabled={isCreatingPR}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              {isCreatingPR ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Creating PR...
                </>
              ) : (
                '✓ Create PR with Selected Model'
              )}
            </button>
          </div>

          {/* Info */}
          <div className="px-6 py-3 bg-blue-50 border-t border-blue-200 text-sm text-blue-800 flex items-start gap-2">
            <span>ℹ️</span>
            <span>
              Compare results from different models and select the best one to create a pull request.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
