'use client';

import React, { useState } from 'react';
import { CodeGeneratorForm, GeneratorFormData } from './CodeGeneratorForm';
import { CodeDiffViewer } from './CodeDiffViewer';
import { MultiModelResults } from './MultiModelResults';

interface GenerationResult {
  original_code: string;
  modified_code: string;
  diff: string;
  instruction: string;
  model: string;
  provider: string;
}

interface MultiModelResult {
  model: string;
  original_code: string;
  modified_code: string;
  diff: string;
  tokens_used?: number;
  generation_time_ms?: number;
  error?: string;
}

interface MultiModelGenerationResult {
  original_code: string;
  instruction: string;
  results: MultiModelResult[];
  models: string[];
  provider: string;
}

type PageState = 'form' | 'generating' | 'result' | 'multi-result' | 'error' | 'creating-pr' | 'pr-created';

interface PageError {
  title: string;
  message: string;
}

interface PRResult {
  prUrl: string;
  prNumber: number;
  branchName: string;
}

export const CodeGeneratorPage: React.FC = () => {
  const [state, setState] = useState<PageState>('form');
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [multiResult, setMultiResult] = useState<MultiModelGenerationResult | null>(null);
  const [error, setError] = useState<PageError | null>(null);
  const [prResult, setPRResult] = useState<PRResult | null>(null);
  const [currentFilePath, setCurrentFilePath] = useState('');
  const [currentRepoUrl, setCurrentRepoUrl] = useState('');
  const [currentInstruction, setCurrentInstruction] = useState('');
  const [currentGitHubToken, setCurrentGitHubToken] = useState('');
  const [currentModifiedCode, setCurrentModifiedCode] = useState('');
  const [currentModel, setCurrentModel] = useState('');
  const [generatingModels, setGeneratingModels] = useState<string[]>([]);

  const handleGenerateCode = async (formData: GeneratorFormData) => {
    setState('generating');
    setError(null);
    setResult(null);
    setMultiResult(null);

    const useMultiModel = formData.useMultiModel && formData.models && formData.models.length > 0;

    if (formData.useMultiModel && formData.models) {
      setGeneratingModels(formData.models);
    } else {
      setGeneratingModels([formData.model || ''].filter(Boolean));
    }

    setCurrentFilePath(formData.filePath);
    setCurrentRepoUrl(formData.repoUrl);
    setCurrentInstruction(formData.instruction);
    setCurrentGitHubToken(formData.githubToken);

    try {
      if (useMultiModel) {
        // Multi-model streaming flow
        const response = await fetch('/api/generate/code-parallel-stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_url: formData.repoUrl,
            file_path: formData.filePath,
            instruction: formData.instruction,
            github_token: formData.githubToken,
            models: formData.models,
            provider: 'huggingface',
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate code');
        }

        if (!response.body) throw new Error('No response body');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let initData: { original_code: string; instruction: string; models: string[]; provider: string } | null = null;
        const streamedResults: MultiModelResult[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (!line.trim()) continue;
            let event;
            try {
              event = JSON.parse(line);
            } catch {
              continue;
            }
            if (event.type === 'error') {
              throw new Error(event.detail || 'Stream error');
            } else if (event.type === 'init') {
              initData = event;
            } else if (event.type === 'result' && initData) {
              streamedResults.push({
                model: event.model,
                original_code: event.original_code,
                modified_code: event.modified_code,
                diff: event.diff,
                tokens_used: event.tokens_used,
                generation_time_ms: event.generation_time_ms,
                error: event.error,
              });
              setMultiResult({
                original_code: initData.original_code,
                instruction: initData.instruction,
                results: [...streamedResults],
                models: initData.models,
                provider: initData.provider,
              });
              setState('multi-result');
            }
          }
        }
      } else {
        // Single-model flow
        const response = await fetch('/api/generate/code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_url: formData.repoUrl,
            file_path: formData.filePath,
            instruction: formData.instruction,
            github_token: formData.githubToken,
            model: formData.model,
            provider: 'huggingface',
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate code');
        }

        const data = await response.json();
        setResult(data);
        setCurrentModifiedCode(data.modified_code);
        setCurrentModel(data.model);
        setState('result');
      }
    } catch (err) {
      setError({
        title: 'Generation Failed',
        message: err instanceof Error ? err.message : 'An unexpected error occurred',
      });
      setState('error');
    }
  };

  const handleCreatePR = async (selectedModel?: string, modifiedCode?: string) => {
    const code = modifiedCode || currentModifiedCode;
    if (!code) return;

    setState('creating-pr');
    setError(null);

    const modelInfo = selectedModel || currentModel;
    const resultInfo = result || (multiResult && selectedModel ? { model: selectedModel, provider: multiResult.provider } : null);

    try {
      const response = await fetch('/api/generate/create-pr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: currentRepoUrl,
          file_path: currentFilePath,
          modified_code: code,
          title: `DevForge: ${currentInstruction.substring(0, 50)}`,
          description: `AI-generated modification:\n\n${currentInstruction}\n\nModel: ${modelInfo}\nProvider: ${resultInfo?.provider || 'huggingface'}`,
          github_token: currentGitHubToken,
          branch_name: `devforge/modify-${Date.now()}`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create PR');
      }

      const prData = await response.json();
      setPRResult(prData);
      setState('pr-created');
    } catch (err) {
      setError({
        title: 'PR Creation Failed',
        message: err instanceof Error ? err.message : 'An unexpected error occurred',
      });
      setState('error');
    }
  };

  const handleReset = () => {
    setState('form');
    setResult(null);
    setMultiResult(null);
    setError(null);
    setPRResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Code Generator</h1>
          <p className="text-lg text-gray-600">
            Use AI to modify your GitHub repositories with a single instruction
          </p>
        </div>

        {/* State: Form */}
        {state === 'form' && (
          <CodeGeneratorForm
            onSubmit={handleGenerateCode}
            isLoading={false}
          />
        )}

        {/* State: Generating */}
        {state === 'generating' && (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="flex justify-center mb-6">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {generatingModels.length > 1 ? `Running ${generatingModels.length} models in parallel...` : 'Generating Code...'}
            </h3>
            {generatingModels.length > 1 ? (
              <div className="mt-4 space-y-2">
                {generatingModels.map(m => (
                  <div key={m} className="inline-flex items-center gap-2 bg-blue-50 text-blue-800 text-sm px-3 py-1 rounded-full mr-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
                    {m.split('/').pop()}
                  </div>
                ))}
                <p className="text-gray-500 text-sm mt-4">Results will appear as each model completes</p>
              </div>
            ) : (
              <p className="text-gray-600">
                {generatingModels[0] ? `Model: ${generatingModels[0].split('/').pop()}` : 'Processing your request...'}
              </p>
            )}
          </div>
        )}

        {/* State: Result */}
        {state === 'result' && result && (
          <div>
            <CodeDiffViewer
              originalCode={result.original_code}
              modifiedCode={result.modified_code}
              diff={result.diff}
              filePath={currentFilePath}
              instruction={currentInstruction}
              onApprove={handleCreatePR}
              isCreatingPR={state === 'creating-pr'}
            />
            <div className="mt-6 text-center">
              <button
                onClick={handleReset}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← Back to Generator
              </button>
            </div>
          </div>
        )}

        {/* State: Multi-Model Result */}
        {state === 'multi-result' && multiResult && (
          <div>
            <MultiModelResults
              results={multiResult.results.map(r => ({
                model: r.model,
                originalCode: r.original_code,
                modifiedCode: r.modified_code,
                diff: r.diff,
                tokensUsed: r.tokens_used,
                generationTimeMs: r.generation_time_ms,
                error: r.error,
              }))}
              instruction={currentInstruction}
              filePath={currentFilePath}
              onSelectModel={handleCreatePR}
              isCreatingPR={state === 'creating-pr'}
            />
            <div className="mt-6 text-center">
              <button
                onClick={handleReset}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← Back to Generator
              </button>
            </div>
          </div>
        )}

        {/* State: Error */}
        {state === 'error' && error && (
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-red-500">
            <div className="flex gap-4">
              <span className="text-red-500 flex-shrink-0 text-2xl">⚠️</span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{error.title}</h3>
                <p className="text-gray-700 mb-4">{error.message}</p>
                <button
                  onClick={handleReset}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* State: PR Created */}
        {state === 'pr-created' && prResult && (
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-green-500">
            <div className="flex gap-4">
              <span className="text-green-500 flex-shrink-0 text-2xl">✓</span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Pull Request Created! 🎉
                </h3>
                <p className="text-gray-700 mb-4">
                  Branch: <code className="bg-gray-100 px-2 py-1 rounded">{prResult.branch_name}</code>
                </p>
                <a
                  href={prResult.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition mb-4"
                >
                  View PR #{prResult.pr_number} on GitHub →
                </a>
                <div>
                  <button
                    onClick={handleReset}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Generate Another
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
