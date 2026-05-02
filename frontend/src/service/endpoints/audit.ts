import api from '../api';

export interface AuditRequest {
  url: string;
  depth?: number;
}

export interface AuditTask {
  task_id: string;
  status: 'processing' | 'completed' | 'failed';
}

export const auditService = {
  startAudit: async (request: AuditRequest): Promise<AuditTask> => {
    const response = await api.post<AuditTask>('/start_audit', request);
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<AuditTask> => {
    const response = await api.get<AuditTask>(`/task/${taskId}`);
    return response.data;
  },
};
