import React, { useState } from 'react';

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

const HF_MODELS = [
  { id: 'deepseek-coder', name: 'DeepSeek Coder (7B)' },
  { id: 'codellama', name: 'CodeLlama (7B)' },
  { id: 'mistral-7b', name: 'Mistral (7B)' },
];

export const CodeGeneratorForm: React.FC<CodeGeneratorFormProps> = ({
  onSubmit,
  isLoading = false
}) => {
  const [formData, setFormData] = useState<GeneratorFormData>({
    repoUrl: '',
    filePath: '',
    instruction: '',
    githubToken: '',
    model: 'deepseek-coder',
    models: ['deepseek-coder'],
    useMultiModel: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showTokenInput, setShowTokenInput] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.repoUrl.trim()) {
      newErrors.repoUrl = 'Repository URL is required';
    } else if (!formData.repoUrl.includes('github.com')) {
      newErrors.repoUrl = 'Must be a GitHub repository URL';
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

        {/* Single Model Selection */}
        {!formData.useMultiModel && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Choose a Model
            </label>
            <select
              value={formData.model}
              onChange={(e) => handleInputChange('model', e.target.value)}
              disabled={isLoading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {HF_MODELS.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
            <p className="text-gray-500 text-xs mt-1">Hugging Face open models</p>
          </div>
        )}

        {/* Multi-Model Selection */}
        {formData.useMultiModel && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Models to Run in Parallel
            </label>
            <div className="space-y-2">
              {HF_MODELS.map(model => (
                <label key={model.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.models?.includes(model.id) || false}
                    onChange={(e) => {
                      const models = formData.models || [];
                      const updated = e.target.checked
                        ? [...models, model.id]
                        : models.filter(m => m !== model.id);
                      setFormData(prev => ({ ...prev, models: updated }));
                      if (errors.models) {
                        setErrors(prev => ({ ...prev, models: '' }));
                      }
                    }}
                    disabled={isLoading}
                    className="disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-700">{model.name}</span>
                </label>
              ))}
            </div>
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
