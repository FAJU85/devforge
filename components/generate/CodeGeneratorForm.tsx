import React, { useState, useEffect } from 'react';

interface CodeGeneratorFormProps {
  onSubmit: (data: GeneratorFormData) => void;
  isLoading?: boolean;
}

export interface GeneratorFormData {
  repoUrl: string;
  filePath: string;
  instruction: string;
  githubToken: string;
  model?: string;
  models?: string[];
  useMultiModel?: boolean;
}

interface ModelMetadata {
  model_id: string;
  name: string;
  downloads: number;
  likes: number;
  url: string;
  architecture?: string;
}

export const CodeGeneratorForm: React.FC<CodeGeneratorFormProps> = ({
  onSubmit,
  isLoading = false
}) => {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [formData, setFormData] = useState<GeneratorFormData>({
    repoUrl: '',
    filePath: '',
    instruction: '',
    githubToken: '',
    model: '',
    models: [],
    useMultiModel: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showTokenInput, setShowTokenInput] = useState(false);

  // Fetch popular models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setModelsLoading(true);
        const response = await fetch('/api/models/popular');
        if (!response.ok) throw new Error('Failed to fetch models');
        const data = await response.json();
        setModels(data.models || []);

        if (data.models && data.models.length > 0) {
          setFormData(prev => ({
            ...prev,
            model: data.models[0].model_id,
            models: [data.models[0].model_id],
          }));
        }
      } catch (err) {
        setModelsError(err instanceof Error ? err.message : 'Failed to load models');
        console.error('Error fetching models:', err);
      } finally {
        setModelsLoading(false);
      }
    };

    fetchModels();
  }, []);

  // Debounced model search — fires only when user actively types a query
  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (!trimmed) return;

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setModelsLoading(true);
        setModelsError(null);
        const response = await fetch(
          `/api/models/discover?query=${encodeURIComponent(trimmed)}&limit=20`,
          { signal: controller.signal },
        );
        if (!response.ok) throw new Error('Search failed');
        const data = await response.json();
        setModels(data.models || []);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setModelsError(err instanceof Error ? err.message : 'Search failed');
      } finally {
        setModelsLoading(false);
      }
    }, 350);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [searchQuery]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.repoUrl.trim()) {
      newErrors.repoUrl = 'Repository URL is required';
    } else {
      try {
        const parsed = new URL(formData.repoUrl.trim());
        if (!['github.com', 'www.github.com'].includes(parsed.hostname)) {
          newErrors.repoUrl = 'Must be a GitHub repository URL';
        }
      } catch {
        newErrors.repoUrl = 'Must be a valid URL';
      }
    }

    if (!formData.filePath.trim()) {
      newErrors.filePath = 'File path is required';
    }

    if (!formData.instruction.trim()) {
      newErrors.instruction = 'Instruction is required';
    } else if (formData.instruction.trim().length < 10) {
      newErrors.instruction = 'Instruction must be at least 10 characters';
    }

    if (formData.useMultiModel) {
      if (!formData.models || formData.models.length === 0) {
        newErrors.models = 'Select at least one model';
      }
    } else {
      if (!formData.model?.trim()) {
        newErrors.model = 'Model is required';
      }
    }

    if (!formData.githubToken.trim()) {
      newErrors.githubToken = 'GitHub token is required';
      setShowTokenInput(true);
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof GeneratorFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Generate or Modify Code</h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Repository URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <input
            type="text"
            placeholder="https://github.com/owner/repo"
            value={formData.repoUrl}
            onChange={(e) => handleInputChange('repoUrl', e.target.value)}
            disabled={isLoading}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition ${
              errors.repoUrl ? 'border-red-500' : 'border-gray-300'
            } disabled:bg-gray-100 disabled:cursor-not-allowed`}
          />
          {errors.repoUrl && (
            <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
              ⚠️ {errors.repoUrl}
            </p>
          )}
        </div>

        {/* File Path */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            File Path (in repository)
          </label>
          <input
            type="text"
            placeholder="src/utils.py"
            value={formData.filePath}
            onChange={(e) => handleInputChange('filePath', e.target.value)}
            disabled={isLoading}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition ${
              errors.filePath ? 'border-red-500' : 'border-gray-300'
            } disabled:bg-gray-100 disabled:cursor-not-allowed`}
          />
          {errors.filePath && (
            <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
              {errors.filePath}
            </p>
          )}
        </div>

        {/* Model Selection Mode */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Model Selection
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                checked={!formData.useMultiModel}
                onChange={() => {
                  setFormData(prev => ({ ...prev, useMultiModel: false }));
                  if (errors.models) {
                    setErrors(prev => ({ ...prev, models: '' }));
                  }
                }}
                disabled={isLoading}
                className="disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">Single Model</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                checked={formData.useMultiModel}
                onChange={() => {
                  setFormData(prev => ({ ...prev, useMultiModel: true }));
                  if (errors.model) {
                    setErrors(prev => ({ ...prev, model: '' }));
                  }
                }}
                disabled={isLoading}
                className="disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">Multiple Models</span>
            </label>
          </div>
        </div>

        {/* Model Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Models
          </label>
          <div className="relative">
            <input
              type="text"
              placeholder="Search Hugging Face models (e.g. starcoder, code, mistral)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              disabled={isLoading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition disabled:bg-gray-100"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-sm"
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <p className="text-gray-500 text-xs mt-1">
            {searchQuery
              ? `Searching for "${searchQuery}" on Hugging Face Hub`
              : 'Leave empty to see popular models'}
          </p>
        </div>

        {/* Single Model Selection */}
        {!formData.useMultiModel && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Choose a Model
            </label>
            {modelsLoading ? (
              <div className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
                Loading models...
              </div>
            ) : modelsError ? (
              <div className="w-full px-4 py-2 border border-red-500 rounded-lg bg-red-50 text-red-600 text-sm">
                {modelsError}
              </div>
            ) : (
              <>
                <select
                  value={formData.model || ''}
                  onChange={(e) => handleInputChange('model', e.target.value)}
                  disabled={isLoading}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Select a model...</option>
                  {models.map(model => (
                    <option key={model.model_id} value={model.model_id}>
                      {model.name} • {model.downloads.toLocaleString()} downloads
                    </option>
                  ))}
                </select>
                {formData.model && (
                  <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-gray-600">
                    {(() => {
                      const selected = models.find(m => m.model_id === formData.model);
                      return selected ? (
                        <>
                          <div>📥 {selected.downloads.toLocaleString()} downloads</div>
                          <div>👍 {selected.likes.toLocaleString()} likes</div>
                          {selected.architecture && <div>🏗️ {selected.architecture}</div>}
                        </>
                      ) : null;
                    })()}
                  </div>
                )}
              </>
            )}
            <p className="text-gray-500 text-xs mt-1">Hugging Face open models</p>
          </div>
        )}

        {/* Multi-Model Selection */}
        {formData.useMultiModel && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Models to Run in Parallel
            </label>
            {modelsLoading ? (
              <div className="p-4 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-sm">
                Loading models...
              </div>
            ) : modelsError ? (
              <div className="p-4 border border-red-500 rounded-lg bg-red-50 text-red-600 text-sm">
                {modelsError}
              </div>
            ) : (
              <>
                <div className="space-y-3 mb-4 max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
                  {models.length === 0 ? (
                    <p className="text-gray-500 text-sm">No models available</p>
                  ) : (
                    models.map(model => (
                      <label
                        key={model.model_id}
                        className="flex items-start gap-3 cursor-pointer p-2 hover:bg-blue-50 rounded transition"
                      >
                        <input
                          type="checkbox"
                          checked={formData.models?.includes(model.model_id) || false}
                          onChange={(e) => {
                            const selectedModels = formData.models || [];
                            const updated = e.target.checked
                              ? [...selectedModels, model.model_id]
                              : selectedModels.filter(m => m !== model.model_id);
                            setFormData(prev => ({ ...prev, models: updated }));
                            if (errors.models) {
                              setErrors(prev => ({ ...prev, models: '' }));
                            }
                          }}
                          disabled={isLoading}
                          className="mt-1 disabled:cursor-not-allowed"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900">{model.name}</div>
                          <div className="text-xs text-gray-600 mt-1 flex gap-4">
                            <span>📥 {model.downloads.toLocaleString()} downloads</span>
                            <span>👍 {model.likes.toLocaleString()} likes</span>
                            {model.architecture && <span>🏗️ {model.architecture}</span>}
                          </div>
                        </div>
                      </label>
                    ))
                  )}
                </div>
                {(formData.models?.length ?? 0) > 0 && (
                  <div className="text-xs text-blue-600 mb-2">
                    ✓ {formData.models?.length} model{formData.models?.length === 1 ? '' : 's'} selected
                  </div>
                )}
              </>
            )}
            {errors.models && (
              <p className="text-red-500 text-sm mt-2">{errors.models}</p>
            )}
            <p className="text-gray-500 text-xs mt-2">Results will show side-by-side for comparison</p>
          </div>
        )}

        {/* Instruction */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What would you like the code to do?
          </label>
          <textarea
            placeholder="Add type hints to all functions, Fix performance issues, Add error handling, etc."
            value={formData.instruction}
            onChange={(e) => handleInputChange('instruction', e.target.value)}
            disabled={isLoading}
            rows={4}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none ${
              errors.instruction ? 'border-red-500' : 'border-gray-300'
            } disabled:bg-gray-100 disabled:cursor-not-allowed`}
          />
          {errors.instruction && (
            <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
              {errors.instruction}
            </p>
          )}
        </div>

        {/* GitHub Token */}
        <div>
          <button
            type="button"
            onClick={() => setShowTokenInput(!showTokenInput)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium mb-2 flex items-center gap-1"
          >
            {showTokenInput ? '✕' : '+'} GitHub Token
          </button>

          {showTokenInput && (
            <div>
              <input
                type="password"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                value={formData.githubToken}
                onChange={(e) => handleInputChange('githubToken', e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition ${
                  errors.githubToken ? 'border-red-500' : 'border-gray-300'
                } disabled:bg-gray-100 disabled:cursor-not-allowed`}
              />
              <p className="text-gray-500 text-xs mt-1">
                Create at: github.com/settings/tokens (needs repo access)
              </p>
              {errors.githubToken && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                      {errors.githubToken}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
        >
          {isLoading ? 'Generating...' : 'Generate Code'}
        </button>
      </form>
    </div>
  );
};
