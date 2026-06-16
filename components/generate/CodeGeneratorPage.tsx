'use client';

import React, { useState, useEffect, useRef } from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface HFModel {
  model_id: string;
  name: string;
  downloads: number;
  likes: number;
}

type ModelStatus = 'idle' | 'generating' | 'done' | 'error';

interface ModelState {
  status: ModelStatus;
  originalCode?: string;
  modifiedCode?: string;
  diff?: string;
  tokensUsed?: number;
  generationTimeMs?: number;
  error?: string;
  creatingPR: boolean;
  prUrl?: string;
  prNumber?: number;
}

interface GitHubUser {
  username: string;
  avatar_url?: string;
}

// ─── Diff renderer ────────────────────────────────────────────────────────────

const DiffView: React.FC<{ diff: string }> = ({ diff }) => {
  if (!diff) return <p className="text-gray-400 text-xs p-4">No changes detected.</p>;
  return (
    <pre className="text-xs font-mono overflow-auto h-full p-3 leading-5">
      {diff.split('\n').map((line, i) => {
        let cls = 'text-gray-300';
        if (line.startsWith('+') && !line.startsWith('+++')) cls = 'text-green-400 bg-green-900/20';
        else if (line.startsWith('-') && !line.startsWith('---')) cls = 'text-red-400 bg-red-900/20';
        else if (line.startsWith('@@')) cls = 'text-blue-400';
        else if (line.startsWith('---') || line.startsWith('+++')) cls = 'text-gray-500';
        return (
          <span key={i} className={`block ${cls}`}>{line || ' '}</span>
        );
      })}
    </pre>
  );
};

// ─── Single model column ──────────────────────────────────────────────────────

const ModelColumn: React.FC<{
  model: string;
  state: ModelState;
  filePath: string;
  onApplyPR: () => void;
  onRemove: () => void;
  isOnlyColumn: boolean;
  selectedForPR?: boolean;
  onTogglePRSelection?: () => void;
  onRetry?: () => void;
}> = ({ model, state, filePath, onApplyPR, onRemove, isOnlyColumn, selectedForPR, onTogglePRSelection, onRetry }) => {
  const [viewMode, setViewMode] = useState<'diff' | 'modified'>('diff');

  const shortName = model.split('/').pop() ?? model;

  const statusBadge = () => {
    if (state.status === 'idle') return null;
    if (state.status === 'generating')
      return <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-300 animate-pulse">generating…</span>;
    if (state.status === 'done')
      return <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/40 text-green-300">done</span>;
    if (state.status === 'error')
      return <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/40 text-red-300">error</span>;
  };

  return (
    <div className="flex flex-col flex-1 min-w-0 border-r border-[#1a2228] last:border-r-0 overflow-hidden">
      {/* Column header */}
      <div className="flex items-center justify-between px-3 py-2 bg-[#131920] border-b border-[#1a2228] shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-mono font-semibold text-gray-200 truncate" title={model}>
            {shortName}
          </span>
          {statusBadge()}
          {state.tokensUsed !== undefined && (
            <span className="text-xs text-gray-500 hidden lg:inline">{state.tokensUsed} tok</span>
          )}
          {state.generationTimeMs !== undefined && (
            <span className="text-xs text-gray-500 hidden lg:inline">
              {state.generationTimeMs < 1000 ? `${state.generationTimeMs}ms` : `${(state.generationTimeMs / 1000).toFixed(1)}s`}
            </span>
          )}
        </div>
        <button
          onClick={onRemove}
          disabled={isOnlyColumn}
          className="text-gray-600 hover:text-gray-300 text-xs px-1 disabled:opacity-30 disabled:cursor-not-allowed"
          title="Remove column"
        >
          ✕
        </button>
      </div>

      {/* View toggle (only when done) */}
      {state.status === 'done' && (
        <div className="flex border-b border-[#1a2228] bg-[#0d1116] shrink-0">
          <button
            onClick={() => setViewMode('diff')}
            className={`flex-1 py-1.5 text-xs font-medium transition ${
              viewMode === 'diff' ? 'text-[#e19200] border-b-2 border-[#e19200]' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Diff
          </button>
          <button
            onClick={() => setViewMode('modified')}
            className={`flex-1 py-1.5 text-xs font-medium transition ${
              viewMode === 'modified' ? 'text-[#e19200] border-b-2 border-[#e19200]' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Modified
          </button>
        </div>
      )}

      {/* Column body */}
      <div className="flex-1 overflow-auto bg-[#0d1116]">
        {state.status === 'idle' && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-600 text-xs text-center px-4">
              Hit <span className="text-[#e19200] font-mono">Run</span> to generate
            </p>
          </div>
        )}

        {state.status === 'generating' && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <div className="w-6 h-6 border-2 border-[#e19200] border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 text-xs">Generating…</p>
          </div>
        )}

        {state.status === 'done' && (
          viewMode === 'diff' ? (
            <DiffView diff={state.diff ?? ''} />
          ) : (
            <pre className="text-xs font-mono text-gray-300 overflow-auto h-full p-3 leading-5 whitespace-pre-wrap">
              {state.modifiedCode}
            </pre>
          )
        )}

        {state.status === 'error' && (
          <div className="p-4 flex flex-col gap-3">
            <p className="text-red-400 text-xs">{state.error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs font-medium px-3 py-1.5 rounded transition
                           bg-yellow-900/20 text-yellow-300 hover:bg-yellow-900/30
                           border border-yellow-900/50"
              >
                Retry
              </button>
            )}
          </div>
        )}
      </div>

      {/* Apply PR footer */}
      {state.status === 'done' && (
        <div className="shrink-0 border-t border-[#1a2228] p-2 bg-[#131920] space-y-2">
          {state.prUrl ? (
            <a
              href={state.prUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center text-xs font-medium py-1.5 px-3 rounded
                         bg-green-900/40 text-green-300 hover:bg-green-900/60 transition"
            >
              PR #{state.prNumber} →
            </a>
          ) : (
            <>
              <button
                onClick={onApplyPR}
                disabled={state.creatingPR}
                className="w-full text-xs font-medium py-1.5 px-3 rounded transition
                           bg-[#e19200]/10 text-[#e19200] hover:bg-[#e19200]/20
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {state.creatingPR ? 'Creating PR…' : 'Apply as PR'}
              </button>
              {onTogglePRSelection && (
                <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer hover:text-gray-300 transition">
                  <input
                    type="checkbox"
                    checked={selectedForPR ?? false}
                    onChange={onTogglePRSelection}
                    className="w-3 h-3 rounded cursor-pointer"
                  />
                  Select for batch
                </label>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Model picker dropdown ─────────────────────────────────────────────────────

const ModelPicker: React.FC<{
  available: HFModel[];
  selected: string[];
  loading: boolean;
  onAdd: (id: string) => void;
  onClose: () => void;
}> = ({ available, selected, loading, onAdd, onClose }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<HFModel[]>([]);
  const [searching, setSearching] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) { setSearchResults([]); return; }
    const controller = new AbortController();
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        const r = await fetch(`/api/models/discover?query=${encodeURIComponent(trimmed)}&limit=10`, { signal: controller.signal });
        if (r.ok) setSearchResults((await r.json()).models ?? []);
      } catch { /* AbortError is fine */ }
      setSearching(false);
    }, 300);
    return () => { controller.abort(); clearTimeout(t); };
  }, [query]);

  const displayList = query.trim() ? searchResults : available;

  return (
    <div
      ref={ref}
      className="absolute top-full left-0 mt-1 w-72 z-50 bg-[#1a2228] border border-[#2a3540]
                 rounded-lg shadow-2xl overflow-hidden"
    >
      <div className="p-2 border-b border-[#2a3540]">
        <input
          autoFocus
          type="text"
          placeholder="Search models…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full text-xs bg-[#0d1116] border border-[#2a3540] rounded px-2 py-1.5
                     text-gray-200 placeholder-gray-600 outline-none focus:border-[#e19200]"
        />
      </div>
      <div className="max-h-56 overflow-y-auto">
        {(loading || searching) && (
          <p className="text-xs text-gray-500 p-3">Loading…</p>
        )}
        {!loading && !searching && displayList.length === 0 && (
          <p className="text-xs text-gray-500 p-3">No results</p>
        )}
        {displayList.map(m => {
          const alreadyAdded = selected.includes(m.model_id);
          return (
            <button
              key={m.model_id}
              onClick={() => { if (!alreadyAdded) onAdd(m.model_id); }}
              disabled={alreadyAdded}
              className={`w-full text-left px-3 py-2 text-xs transition ${
                alreadyAdded
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-200 hover:bg-[#2a3540]'
              }`}
            >
              <span className="font-mono">{m.model_id.split('/').pop()}</span>
              <span className="text-gray-500 ml-1 text-[10px]">{m.downloads.toLocaleString()} dl</span>
              {alreadyAdded && <span className="text-gray-600 ml-1">✓</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
};

// ─── Main page ────────────────────────────────────────────────────────────────

export const CodeGeneratorPage: React.FC = () => {
  const [instruction, setInstruction] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [filePath, setFilePath] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelStates, setModelStates] = useState<Record<string, ModelState>>({});
  const [availableModels, setAvailableModels] = useState<HFModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [showPicker, setShowPicker] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [githubUser, setGithubUser] = useState<GitHubUser | null>(null);
  const [selectedForPR, setSelectedForPR] = useState<Set<string>>(new Set());
  const [batchCreatingPRs, setBatchCreatingPRs] = useState(false);
  const [generationState, setGenerationState] = useState<{
    fileContent: string;
    originalCode: string;
  } | null>(null);

  // Load popular models on mount
  useEffect(() => {
    fetch('/api/models/popular')
      .then(r => r.ok ? r.json() : { models: [] })
      .then(data => {
        const models: HFModel[] = data.models ?? [];
        setAvailableModels(models);
        if (models.length > 0) {
          const defaultPick = models.slice(0, 3).map((m: HFModel) => m.model_id);
          setSelectedModels(defaultPick);
        }
        setModelsLoading(false);
      })
      .catch(() => setModelsLoading(false));
  }, []);

  // Check GitHub session
  useEffect(() => {
    fetch('/api/auth/github/me')
      .then(r => r.ok ? r.json() : null)
      .then(data => setGithubUser(data))
      .catch(() => {});
  }, []);

  const setModelState = (model: string, patch: Partial<ModelState>) => {
    setModelStates(prev => ({
      ...prev,
      [model]: { creatingPR: false, status: 'idle', ...prev[model], ...patch },
    }));
  };

  const addModel = (id: string) => {
    if (!selectedModels.includes(id)) {
      setSelectedModels(prev => [...prev, id]);
    }
    setShowPicker(false);
  };

  const removeModel = (id: string) => {
    setSelectedModels(prev => prev.filter(m => m !== id));
    setModelStates(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const validate = (): string | null => {
    if (!repoUrl.trim()) return 'Repository URL is required';
    try {
      const u = new URL(repoUrl.trim());
      const host = u.hostname.toLowerCase();
      if (!/^(www\.)?github\.com$/.test(host)) return 'Must be a GitHub repository URL';
    } catch {
      return 'Must be a valid URL';
    }
    if (!filePath.trim()) return 'File path is required';
    if (!instruction.trim() || instruction.trim().length < 10)
      return 'Instruction must be at least 10 characters';
    if (selectedModels.length === 0) return 'Select at least one model';
    return null;
  };

  const handleGenerate = async () => {
    const err = validate();
    if (err) { setFormError(err); return; }
    setFormError(null);
    setIsGenerating(true);

    // Set all columns to generating with clean state
    selectedModels.forEach(m => setModelState(m, {
      status: 'generating',
      error: undefined,
      prUrl: undefined,
      prNumber: undefined,
    }));

    try {
      const resp = await fetch('/api/generate/code-parallel-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          file_path: filePath.trim(),
          instruction: instruction.trim(),
          github_token: '',
          models: selectedModels,
          provider: 'huggingface',
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        const msg = errData.detail || `HTTP ${resp.status}`;
        selectedModels.forEach(m => setModelState(m, { status: 'error', error: msg }));
        return;
      }

      if (!resp.body) {
        throw new Error('No response body');
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.trim()) continue;

          try {
            const event = JSON.parse(line);

            if (event.type === 'init') {
              // Initial metadata, already set up
            } else if (event.type === 'result') {
              const model = event.model;
              if (event.error) {
                setModelState(model, {
                  status: 'error',
                  error: event.error,
                  generationTimeMs: event.generation_time_ms,
                });
              } else {
                setModelState(model, {
                  status: 'done',
                  originalCode: event.original_code,
                  modifiedCode: event.modified_code,
                  diff: event.diff,
                  tokensUsed: event.tokens_used,
                  generationTimeMs: event.generation_time_ms,
                  error: undefined,
                });
              }
            } else if (event.type === 'error') {
              const msg = event.detail || 'Stream error';
              selectedModels.forEach(m => setModelState(m, { status: 'error', error: msg }));
              break;
            }
          } catch (e) {
            console.error('Failed to parse stream event:', e);
          }
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      selectedModels.forEach(m => setModelState(m, { status: 'error', error: msg }));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplyPR = async (model: string) => {
    const state = modelStates[model];
    if (!state?.modifiedCode) return;
    setModelState(model, { creatingPR: true });

    try {
      const resp = await fetch('/api/generate/create-pr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          file_path: filePath.trim(),
          modified_code: state.modifiedCode,
          title: `DevForge: ${instruction.substring(0, 50)}`,
          description: `AI-generated modification\n\n**Instruction:** ${instruction}\n**Model:** ${model}\n**Provider:** huggingface`,
          branch_name: `devforge/${model.split('/').pop()}-${Date.now()}`,
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${resp.status}`);
      }

      const pr = await resp.json();
      setModelState(model, { creatingPR: false, prUrl: pr.pr_url, prNumber: pr.pr_number });
    } catch (e) {
      setModelState(model, {
        status: 'error',
        creatingPR: false,
        error: e instanceof Error ? e.message : 'PR creation failed',
      });
    }
  };

  const handleBatchCreatePRs = async () => {
    if (selectedForPR.size === 0) return;
    setBatchCreatingPRs(true);

    for (const model of selectedForPR) {
      const state = modelStates[model];
      if (!state?.modifiedCode || state.prUrl) continue;

      setModelState(model, { creatingPR: true });

      try {
        const resp = await fetch('/api/generate/create-pr', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_url: repoUrl.trim(),
            file_path: filePath.trim(),
            modified_code: state.modifiedCode,
            title: `DevForge: ${instruction.substring(0, 50)}`,
            description: `AI-generated modification\n\n**Instruction:** ${instruction}\n**Model:** ${model}\n**Provider:** huggingface`,
            branch_name: `devforge/${model.split('/').pop()}-${Date.now()}`,
          }),
        });

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${resp.status}`);
        }

        const pr = await resp.json();
        setModelState(model, { creatingPR: false, prUrl: pr.pr_url, prNumber: pr.pr_number });
      } catch (e) {
        setModelState(model, {
          status: 'error',
          creatingPR: false,
          error: e instanceof Error ? e.message : 'PR creation failed',
        });
      }
    }

    setSelectedForPR(new Set());
    setBatchCreatingPRs(false);
  };

  const handleRetry = async (model: string) => {
    setModelState(model, {
      status: 'generating',
      error: undefined,
    });

    try {
      const resp = await fetch('/api/generate/code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          file_path: filePath.trim(),
          instruction: instruction.trim(),
          github_token: '',
          model: model,
          provider: 'huggingface',
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        const msg = errData.detail || `HTTP ${resp.status}`;
        setModelState(model, { status: 'error', error: msg });
        return;
      }

      const data = await resp.json();
      setModelState(model, {
        status: 'done',
        originalCode: data.original_code,
        modifiedCode: data.modified_code,
        diff: data.diff,
        error: undefined,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setModelState(model, { status: 'error', error: msg });
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1116]">

      {/* ── Top input bar ─────────────────────────────────────────────────── */}
      <div className="shrink-0 px-4 pt-4 pb-3 bg-[#131920] border-b border-[#1a2228] space-y-3">

        {/* Instruction */}
        <textarea
          value={instruction}
          onChange={e => { setInstruction(e.target.value); setFormError(null); }}
          placeholder="Describe what you want the AI to do… (e.g. Add type hints to all functions)"
          rows={2}
          className="w-full text-sm bg-[#0d1116] border border-[#1a2228] rounded-lg px-3 py-2
                     text-gray-200 placeholder-gray-600 outline-none resize-none
                     focus:border-[#e19200] transition"
        />

        {/* Repo + File + Models + Run */}
        <div className="flex flex-wrap gap-2 items-end">
          {/* Repo URL */}
          <div className="flex flex-col gap-1 flex-1 min-w-48">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Repository</label>
            <input
              type="text"
              value={repoUrl}
              onChange={e => { setRepoUrl(e.target.value); setFormError(null); }}
              placeholder="https://github.com/owner/repo"
              className="text-xs bg-[#0d1116] border border-[#1a2228] rounded px-2 py-1.5
                         text-gray-200 placeholder-gray-600 outline-none
                         focus:border-[#e19200] transition"
            />
          </div>

          {/* File path */}
          <div className="flex flex-col gap-1 w-48">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">File path</label>
            <input
              type="text"
              value={filePath}
              onChange={e => { setFilePath(e.target.value); setFormError(null); }}
              placeholder="src/routes.py"
              className="text-xs bg-[#0d1116] border border-[#1a2228] rounded px-2 py-1.5
                         text-gray-200 placeholder-gray-600 outline-none
                         focus:border-[#e19200] transition"
            />
          </div>

          {/* Model chips + picker */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Models</label>
            <div className="flex flex-wrap gap-1 items-center relative">
              {selectedModels.map(m => (
                <span
                  key={m}
                  className="flex items-center gap-1 text-xs bg-[#1a2228] border border-[#2a3540]
                             text-gray-300 rounded px-2 py-0.5"
                >
                  <span className="font-mono">{m.split('/').pop()}</span>
                  <button
                    onClick={() => removeModel(m)}
                    disabled={selectedModels.length <= 1}
                    className="text-gray-600 hover:text-gray-300 disabled:opacity-30 text-[10px] ml-0.5"
                  >
                    ✕
                  </button>
                </span>
              ))}
              <div className="relative">
                <button
                  onClick={() => setShowPicker(!showPicker)}
                  className="text-xs px-2 py-0.5 rounded border border-dashed border-[#2a3540]
                             text-gray-500 hover:text-gray-300 hover:border-gray-500 transition"
                >
                  + add
                </button>
                {showPicker && (
                  <ModelPicker
                    available={availableModels}
                    selected={selectedModels}
                    loading={modelsLoading}
                    onAdd={addModel}
                    onClose={() => setShowPicker(false)}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Run button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="self-end px-5 py-1.5 text-sm font-semibold rounded-lg transition
                       bg-[#e19200] text-black hover:bg-[#f0a500]
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? 'Running…' : 'Run'}
          </button>
        </div>

        {/* Error + GitHub status */}
        <div className="flex items-center justify-between">
          {formError ? (
            <p className="text-red-400 text-xs">{formError}</p>
          ) : (
            <span />
          )}
          {!githubUser ? (
            <a
              href="/api/auth/github/login"
              className="text-xs text-gray-500 hover:text-gray-300 transition"
            >
              Sign in with GitHub to create PRs →
            </a>
          ) : (
            <span className="text-xs text-gray-500">
              GitHub: <span className="text-gray-300">{githubUser.username}</span>
            </span>
          )}
        </div>
      </div>

      {/* ── 3-column results area ──────────────────────────────────────────── */}
      {selectedModels.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-600 text-sm">Add a model to get started</p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Batch PR button (when models are done and some are selected) */}
          {selectedForPR.size > 0 && (
            <div className="shrink-0 px-4 py-2 bg-[#131920] border-b border-[#1a2228] flex items-center justify-between">
              <span className="text-xs text-gray-400">
                {selectedForPR.size} selected for PR
              </span>
              <button
                onClick={handleBatchCreatePRs}
                disabled={batchCreatingPRs}
                className="text-xs font-medium px-3 py-1 rounded transition
                           bg-[#e19200]/20 text-[#e19200] hover:bg-[#e19200]/30
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {batchCreatingPRs ? 'Creating…' : `Create ${selectedForPR.size} PR${selectedForPR.size > 1 ? 's' : ''}`}
              </button>
            </div>
          )}
          <div className="flex-1 flex overflow-hidden">
            {selectedModels.map(model => (
              <ModelColumn
                key={model}
                model={model}
                state={modelStates[model] ?? { status: 'idle', creatingPR: false }}
                filePath={filePath}
                onApplyPR={() => handleApplyPR(model)}
                onRemove={() => removeModel(model)}
                isOnlyColumn={selectedModels.length === 1}
                selectedForPR={selectedForPR.has(model)}
                onTogglePRSelection={() => {
                  const next = new Set(selectedForPR);
                  if (next.has(model)) {
                    next.delete(model);
                  } else {
                    next.add(model);
                  }
                  setSelectedForPR(next);
                }}
                onRetry={() => handleRetry(model)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
