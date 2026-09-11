import {
  MOCK_DEVICE_TYPES,
  MOCK_RULES,
  MOCK_SCAN_SUMMARY,
  MOCK_DEVICES,
  MOCK_DEVICE_RESULTS
} from '../data/mockData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const USE_MOCK = true; // Set to false to use real backend once available

export async function apiRequest(path, options = {}) {
  if (USE_MOCK) {
    return handleMockRequest(path, options);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message = body?.error?.message || "The request could not be completed.";
    const error = new Error(message);
    error.status = response.status;
    error.code = body?.error?.code;
    error.details = body?.error?.details || [];
    throw error;
  }

  return body;
}

// Mock request handler
async function handleMockRequest(path, options) {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 800));

  if (path === '/api/device-types') {
    return MOCK_DEVICE_TYPES;
  }
  
  if (path === '/api/rules') {
    return MOCK_RULES;
  }

  if (path === '/api/scans' && options.method === 'POST') {
    return {
      data: {
        scan: MOCK_SCAN_SUMMARY.data
      },
      error: null,
      request_id: "req-mock-post"
    };
  }

  if (path.match(/^\/api\/scans\/[^/]+$/)) {
    return MOCK_SCAN_SUMMARY;
  }

  if (path.match(/^\/api\/scans\/[^/]+\/devices$/)) {
    return MOCK_DEVICES;
  }

  const deviceMatch = path.match(/^\/api\/scans\/[^/]+\/devices\/([^/]+)$/);
  if (deviceMatch) {
    const deviceId = deviceMatch[1];
    if (MOCK_DEVICE_RESULTS[deviceId]) {
      return MOCK_DEVICE_RESULTS[deviceId];
    } else {
      throw new Error("Device not found in mock data");
    }
  }
  
  const ruleMatch = path.match(/^\/api\/rules\/([^/]+)$/);
  if (ruleMatch) {
     const ruleId = ruleMatch[1];
     const rule = MOCK_RULES.data.rules.find(r => r.id === ruleId);
     if (rule) {
         return { data: rule, error: null, request_id: "req-mock-rule" };
     }
     throw new Error("Rule not found");
  }

  throw new Error(`Mock endpoint not found for ${path}`);
}

export async function getDeviceTypes() {
  return apiRequest('/api/device-types');
}

export async function createScan(deviceType, files) {
  const formData = new FormData();
  formData.append("device_type", deviceType);
  files.forEach((file) => formData.append("files", file));

  return apiRequest("/api/scans", {
    method: "POST",
    body: formData,
  });
}

export async function getScan(scanId) {
  return apiRequest(`/api/scans/${scanId}`);
}

export async function getDevices(scanId) {
  return apiRequest(`/api/scans/${scanId}/devices`);
}

export async function getDevice(scanId, deviceId, filters = {}) {
  // Note: filters not fully implemented in mock, but parameter included as requested
  return apiRequest(`/api/scans/${scanId}/devices/${deviceId}`);
}

export async function getRules(filters = {}) {
  return apiRequest('/api/rules');
}

export async function getRule(ruleId) {
  return apiRequest(`/api/rules/${ruleId}`);
}

export function getCsvReportUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/report.csv`;
}

export function getHtmlReportUrl(scanId) {
  return `${API_BASE_URL}/api/scans/${scanId}/report.html`;
}
