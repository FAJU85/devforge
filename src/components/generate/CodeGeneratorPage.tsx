'use client';

import React, { useState } from 'react';
import { CodeGeneratorForm, GeneratorFormData } from './CodeGeneratorForm';
import { CodeDiffViewer } from './CodeDiffViewer';

interface GenerationResult {
  originalCode: string;
  modifiedCode: string;
  diff: string;
  instruction: string;
  model: string;
  provider: string;
}

type PageState = 'form' | 'generating' | 'result' | 'error' | 'creating-pr' | 'pr-created';

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
  const [error, setError] = useState<PageError | null>(null);
  const [prResult, setPRResult] = useState<PRResult | null>(null);
  const [currentFilePath, setCurrentFilePath] = useState('');
  const [currentRepoUrl, setCurrentRepoUrl] = useState('');
  const [currentInstruction, setCurrentInstruction] = useState('');
  const [currentGitHubToken, setCurrentGitHubToken] = useState('');
  const [currentModifiedCode, setCurrentModifiedCode] = useState('');

  const handleGenerateCode = async (formData: GeneratorFormData) => {
    setState('generating');
    setError(null);
    setResult(null);

    try {
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
      setCurrentFilePath(formData.filePath);
      setCurrentRepoUrl(formData.repoUrl);
      setCurrentInstruction(formData.instruction);
      setCurrentGitHubToken(formData.githubToken);
      setCurrentModifiedCode(data.modified_code);
      setState('result');
    } catch (err) {
      setError({
        title: 'Generation Failed',
        message: err instanceof Error ? err.message : 'An unexpected error occurred',
      });
      setState('error');
    }
  };

  const handleCreatePR = async () => {
    if (!result || !currentModifiedCode) return;

    setState('creating-pr');
    setError(null);

    try {
      const response = await fetch('/api/generate/create-pr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: currentRepoUrl,
          file_path: currentFilePath,
          modified_code: currentModifiedCode,
          title: `DevForge: ${currentInstruction.substring(0, 50)}`,
          description: `AI-generated modification:\n\n${currentInstruction}\n\nModel: ${result.model}\nProvider: ${result.provider}`,
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
            <div className="inline-block animate-spin mb-4">
              <div className="text-4xl">⏳</div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Generating Code...</h3>
            <p className="text-gray-600">
              This may take a moment while the AI model processes your request
            </p>
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
              isCreatingPR={false}
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
