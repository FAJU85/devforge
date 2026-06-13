'use client';

import { useState, useEffect } from 'react';

interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'dir' | 'symlink';
  size: number;
  url: string;
  download_url?: string;
}

interface FileContent {
  name: string;
  path: string;
  size: number;
  type: string;
  content: string;
  url: string;
}

interface FileBrowserProps {
  token: string;
  owner: string;
  repo: string;
  branch?: string;
  initialPath?: string;
}

export default function FileBrowser({
  token,
  owner,
  repo,
  branch = 'main',
  initialPath = '',
}: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [error, setError] = useState('');
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);

  useEffect(() => {
    loadDirectory();
    updateBreadcrumbs();
  }, [currentPath, token, owner, repo, branch]);

  const updateBreadcrumbs = () => {
    const parts = currentPath.split('/').filter((p) => p);
    setBreadcrumbs(['', ...parts]);
  };

  const loadDirectory = async () => {
    if (!token || !owner || !repo) {
      setError('Missing required parameters');
      return;
    }

    setLoading(true);
    setError('');
    setFiles([]);

    try {
      const response = await fetch('/api/repositories/files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          owner,
          repo,
          path: currentPath,
          branch,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to load files');
      }

      const data = await response.json();
      setFiles(
        (data.files || []).sort((a: FileItem, b: FileItem) => {
          // Directories first, then alphabetically
          if (a.type === 'dir' && b.type !== 'dir') return -1;
          if (a.type !== 'dir' && b.type === 'dir') return 1;
          return a.name.localeCompare(b.name);
        })
      );
      setSelectedFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFile = async (path: string) => {
    if (!token || !owner || !repo) {
      setError('Missing required parameters');
      return;
    }

    setFileLoading(true);
    setError('');

    try {
      const response = await fetch('/api/repositories/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          owner,
          repo,
          path,
          branch,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to load file');
      }

      const data = await response.json();
      setSelectedFile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file');
    } finally {
      setFileLoading(false);
    }
  };

  const handleFileClick = (file: FileItem) => {
    if (file.type === 'dir') {
      const newPath = currentPath ? `${currentPath}/${file.name}` : file.name;
      setCurrentPath(newPath);
    } else if (file.type === 'file') {
      loadFile(file.path);
    }
  };

  const navigateTo = (index: number) => {
    if (index === 0) {
      setCurrentPath('');
    } else {
      const parts = breadcrumbs.slice(1, index + 1);
      setCurrentPath(parts.join('/'));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="flex h-full gap-4 overflow-hidden">
      {/* File List Pane */}
      <div className="flex flex-1 flex-col overflow-hidden border-r border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 p-4 dark:border-gray-700">
          <h3 className="mb-3 text-lg font-semibold">Repository Files</h3>

          {/* Breadcrumb Navigation */}
          <div className="flex flex-wrap items-center gap-1 text-sm">
            {breadcrumbs.map((part, index) => (
              <div key={index} className="flex items-center gap-1">
                {index > 0 && <span className="text-gray-400">/</span>}
                <button
                  onClick={() => navigateTo(index)}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {part || 'root'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto">
          {error && (
            <div className="m-4 rounded-lg bg-red-100 p-3 text-red-800 dark:bg-red-900 dark:text-red-200">
              {error}
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center p-8">
              <p className="text-gray-600 dark:text-gray-400">Loading files...</p>
            </div>
          )}

          {!loading && files.length === 0 && !error && (
            <div className="flex items-center justify-center p-8">
              <p className="text-gray-600 dark:text-gray-400">No files in this directory</p>
            </div>
          )}

          {!loading && files.length > 0 && (
            <div className="space-y-1 p-2">
              {files.map((file) => (
                <button
                  key={file.path}
                  onClick={() => handleFileClick(file)}
                  className={`w-full text-left rounded px-3 py-2 text-sm transition-colors ${
                    selectedFile?.path === file.path
                      ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {file.type === 'dir' ? (
                      <span>📁</span>
                    ) : (
                      <span>📄</span>
                    )}
                    <span className="flex-1 truncate">{file.name}</span>
                    {file.type === 'file' && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatFileSize(file.size)}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* File Content Pane */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {selectedFile ? (
          <>
            {/* File Header */}
            <div className="flex-shrink-0 border-b border-gray-200 p-4 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-mono text-sm font-semibold truncate">
                  {selectedFile.name}
                </h4>
                {selectedFile.url && (
                  <a
                    href={selectedFile.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                  >
                    View on GitHub →
                  </a>
                )}
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {selectedFile.path} • {formatFileSize(selectedFile.size)}
              </p>
            </div>

            {/* File Content */}
            <div className="flex-1 overflow-auto bg-gray-50 p-4 dark:bg-gray-900">
              {fileLoading ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-600 dark:text-gray-400">Loading file...</p>
                </div>
              ) : (
                <pre className="font-mono text-xs whitespace-pre-wrap break-words">
                  {selectedFile.content}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-gray-600 dark:text-gray-400">
              Select a file to view its contents
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
