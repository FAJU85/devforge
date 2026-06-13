import React from 'react';
import { Settings, Key, Bell, Shield, Database } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
          Settings
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Configure your DevForge platform
        </p>
      </div>

      {/* API Keys Section */}
      <SettingsSection
        icon={<Key className="w-5 h-5" />}
        title="API Keys"
        description="Manage your API keys and credentials"
      >
        <div className="space-y-4">
          <SettingItem
            label="Anthropic API Key"
            value="sk-ant-•••••••••••••"
            masked={true}
          />
          <SettingItem
            label="OpenAI API Key"
            value="sk-•••••••••••••"
            masked={true}
          />
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition">
              Update Keys
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* Notifications Section */}
      <SettingsSection
        icon={<Bell className="w-5 h-5" />}
        title="Notifications"
        description="Manage notification preferences"
      >
        <div className="space-y-4">
          <ToggleSetting
            label="Task Completion Alerts"
            description="Notify when tasks complete"
            enabled={true}
          />
          <ToggleSetting
            label="Error Notifications"
            description="Notify on task failures"
            enabled={true}
          />
          <ToggleSetting
            label="Weekly Reports"
            description="Send weekly performance reports"
            enabled={false}
          />
        </div>
      </SettingsSection>

      {/* Database Section */}
      <SettingsSection
        icon={<Database className="w-5 h-5" />}
        title="Database"
        description="Database and storage configuration"
      >
        <div className="space-y-4">
          <SettingItem
            label="PostgreSQL Host"
            value="localhost:5432"
            editable={true}
          />
          <SettingItem
            label="Milvus Host"
            value="localhost:19530"
            editable={true}
          />
          <SettingItem
            label="MinIO Endpoint"
            value="localhost:9000"
            editable={true}
          />
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <button className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition">
              Test Connection
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* Security Section */}
      <SettingsSection
        icon={<Shield className="w-5 h-5" />}
        title="Security"
        description="Security and access control"
      >
        <div className="space-y-4">
          <ToggleSetting
            label="Enable Authentication"
            description="Require login to access dashboard"
            enabled={false}
          />
          <ToggleSetting
            label="Enable Rate Limiting"
            description="Limit API requests per minute"
            enabled={false}
          />
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-900 dark:text-blue-300">
              💡 Production deployment requires authentication and HTTPS
            </p>
          </div>
        </div>
      </SettingsSection>

      {/* Agent Configuration */}
      <SettingsSection
        icon={<Settings className="w-5 h-5" />}
        title="Agent Configuration"
        description="Configure agent parameters"
      >
        <div className="space-y-4">
          <SettingItem
            label="Max Steps per Task"
            value="50"
            type="number"
          />
          <SettingItem
            label="Task Timeout (seconds)"
            value="300"
            type="number"
          />
          <SettingItem
            label="Max Concurrent Tasks"
            value="5"
            type="number"
          />
          <SettingItem
            label="Browser Type"
            value="chromium"
            type="select"
            options={['chromium', 'firefox', 'webkit']}
          />
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <button className="px-4 py-2 bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-medium hover:bg-slate-300 dark:hover:bg-slate-700 transition">
              Save Changes
            </button>
          </div>
        </div>
      </SettingsSection>

      {/* Danger Zone */}
      <div className="dev-card border-red-200 dark:border-red-800">
        <h3 className="text-lg font-semibold text-red-900 dark:text-red-300 flex items-center gap-2 mb-4">
          <span className="text-xl">⚠️</span> Danger Zone
        </h3>
        <div className="space-y-3">
          <button className="w-full px-4 py-2 border border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg font-medium transition">
            Clear All Task History
          </button>
          <button className="w-full px-4 py-2 border border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg font-medium transition">
            Reset to Default Settings
          </button>
        </div>
      </div>
    </div>
  );
}

function SettingsSection({ icon, title, description, children }) {
  return (
    <div className="dev-card">
      <div className="flex items-start gap-3 mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
        <div className="text-[#76cd1d] mt-1">{icon}</div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            {title}
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {description}
          </p>
        </div>
      </div>
      {children}
    </div>
  );
}

function SettingItem({ label, value, masked = false, editable = false, type = 'text', options = [] }) {
  return (
    <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
      <div>
        <p className="text-sm font-medium text-slate-900 dark:text-white">
          {label}
        </p>
      </div>
      {type === 'select' ? (
        <select
          defaultValue={value}
          className="px-3 py-1 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white text-sm"
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : editable ? (
        <input
          type={type}
          defaultValue={value}
          className="px-3 py-1 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white text-sm"
        />
      ) : (
        <code
          className={`text-sm font-mono ${
            masked ? 'text-slate-600' : 'text-[#76cd1d]'
          }`}
        >
          {value}
        </code>
      )}
    </div>
  );
}

function ToggleSetting({ label, description, enabled = false }) {
  return (
    <div className="flex items-start justify-between p-4 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
      <div>
        <p className="font-medium text-slate-900 dark:text-white">{label}</p>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          {description}
        </p>
      </div>
      <button
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
          enabled ? 'bg-[#76cd1d]' : 'bg-slate-300 dark:bg-slate-600'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
            enabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}
