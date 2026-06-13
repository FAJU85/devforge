/**
 * Hugging Face Hub API Client - interactions with Hugging Face models and datasets
 */

import { ApiClient, ApiResponse, ApiConfig } from './client';

export interface HFModel {
  id: string;
  author: string;
  private: boolean;
  disabled: boolean;
  downloads: number;
  lastModified: string;
  tags: string[];
  siblings: Array<{ rfilename: string; size?: number }>;
}

export interface HFDataset {
  id: string;
  author: string;
  private: boolean;
  disabled: boolean;
  downloads: number;
  lastModified: string;
  tags: string[];
}

export interface HFSpace {
  id: string;
  author: string;
  private: boolean;
  stage: string;
  runtime?: {
    stage: string;
    sdk: string;
    hardware?: string;
  };
  lastModified: string;
}

export interface HFModelInfo {
  modelId: string;
  author: string;
  description?: string;
  downloads: number;
  likes: number;
  private: boolean;
  disabled: boolean;
  lastModified: string;
  tags: string[];
  pipeline_tag?: string;
  library_name?: string;
}

export interface HFSearchResult {
  models?: HFModel[];
  datasets?: HFDataset[];
  spaces?: HFSpace[];
  total: number;
}

export class HuggingFaceClient extends ApiClient {
  constructor(token?: string) {
    const config: ApiConfig = {
      baseUrl: 'https://huggingface.co/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (token) {
      config.headers!['Authorization'] = `Bearer ${token}`;
    }

    super(config);
  }

  async searchModels(
    query: string,
    limit: number = 20,
    skip: number = 0,
    filter?: { task?: string; library?: string; language?: string }
  ): Promise<ApiResponse<HFModel[]>> {
    let url = `/models?search=${encodeURIComponent(query)}&limit=${limit}&skip=${skip}`;

    if (filter?.task) {
      url += `&task=${encodeURIComponent(filter.task)}`;
    }
    if (filter?.library) {
      url += `&library=${encodeURIComponent(filter.library)}`;
    }
    if (filter?.language) {
      url += `&language=${encodeURIComponent(filter.language)}`;
    }

    return this.get<HFModel[]>(url);
  }

  async getModel(modelId: string): Promise<ApiResponse<HFModelInfo>> {
    return this.get<HFModelInfo>(`/models/${encodeURIComponent(modelId)}`);
  }

  async getModelInfo(modelId: string): Promise<ApiResponse<any>> {
    return this.get<any>(`/models/${encodeURIComponent(modelId)}/info`);
  }

  async listModelFiles(modelId: string): Promise<ApiResponse<any[]>> {
    return this.get<any[]>(`/models/${encodeURIComponent(modelId)}/tree`);
  }

  async getModelFile(modelId: string, filename: string): Promise<ApiResponse<any>> {
    return this.get<any>(
      `/models/${encodeURIComponent(modelId)}/raw/${encodeURIComponent(filename)}`
    );
  }

  async searchDatasets(
    query: string,
    limit: number = 20,
    skip: number = 0,
    filter?: { task?: string; language?: string }
  ): Promise<ApiResponse<HFDataset[]>> {
    let url = `/datasets?search=${encodeURIComponent(query)}&limit=${limit}&skip=${skip}`;

    if (filter?.task) {
      url += `&task=${encodeURIComponent(filter.task)}`;
    }
    if (filter?.language) {
      url += `&language=${encodeURIComponent(filter.language)}`;
    }

    return this.get<HFDataset[]>(url);
  }

  async getDataset(datasetId: string): Promise<ApiResponse<HFDataset>> {
    return this.get<HFDataset>(`/datasets/${encodeURIComponent(datasetId)}`);
  }

  async searchSpaces(
    query: string,
    limit: number = 20,
    skip: number = 0
  ): Promise<ApiResponse<HFSpace[]>> {
    return this.get<HFSpace[]>(
      `/spaces?search=${encodeURIComponent(query)}&limit=${limit}&skip=${skip}`
    );
  }

  async getSpace(spaceId: string): Promise<ApiResponse<HFSpace>> {
    return this.get<HFSpace>(`/spaces/${encodeURIComponent(spaceId)}`);
  }

  async getTrendingModels(limit: number = 20): Promise<ApiResponse<HFModel[]>> {
    return this.get<HFModel[]>(`/models?sort=trending&limit=${limit}`);
  }

  async getNewestModels(limit: number = 20): Promise<ApiResponse<HFModel[]>> {
    return this.get<HFModel[]>(`/models?sort=newest&limit=${limit}`);
  }

  async getMostDownloadedModels(limit: number = 20): Promise<ApiResponse<HFModel[]>> {
    return this.get<HFModel[]>(`/models?sort=downloads&limit=${limit}`);
  }

  async searchByTask(task: string, limit: number = 20): Promise<ApiResponse<HFModel[]>> {
    return this.get<HFModel[]>(`/models?task=${encodeURIComponent(task)}&limit=${limit}`);
  }

  async listModelTags(): Promise<ApiResponse<string[]>> {
    return this.get<string[]>('/models?tags=true');
  }

  async getModelDownloads(
    modelId: string,
    period: 'day' | 'week' | 'month' = 'month'
  ): Promise<ApiResponse<any>> {
    return this.get<any>(
      `/models/${encodeURIComponent(modelId)}/downloads?period=${period}`
    );
  }

  async searchCommunity(
    query: string,
    resourceType: 'model' | 'dataset' | 'space' = 'model'
  ): Promise<ApiResponse<any>> {
    const encoded = encodeURIComponent(query);
    return this.get<any>(`/search?q=${encoded}&type=${resourceType}`);
  }

  async validateModelId(modelId: string): Promise<ApiResponse<{ valid: boolean }>> {
    return this.get<{ valid: boolean }>(
      `/models/${encodeURIComponent(modelId)}/validate`
    );
  }

  async checkModelAccess(modelId: string): Promise<ApiResponse<{ accessible: boolean }>> {
    return this.get<{ accessible: boolean }>(
      `/models/${encodeURIComponent(modelId)}/access`
    );
  }
}
