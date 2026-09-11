import {
  MOCK_DEVICE_TYPES,
  MOCK_RULES,
  MOCK_SCAN_SUMMARY,
  MOCK_DEVICES,
  MOCK_DEVICE_RESULTS
} from '../data/mockData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function apiRequest(path, options = {}) {
  if (USE_MOCK) {
    return handleMockRequest(path, options);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (networkErr) {
    const error = new Error(
      `Cannot connect to Phoenix Protocol backend at ${API_BASE_URL}. Ensure the backend service is running.`
    );
    error.status = 0;
    error.code = "NETWORK_ERROR";
    error.details = [networkErr.message];
    throw error;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      body?.error?.message ||
      `Request failed with status ${response.status} (${response.statusText || "Error"}).`;
    const error = new Error(message);
    error.status = response.status;
    error.code = body?.error?.code || `HTTP_${response.status}`;
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

  if (path === '/api/contact' && options.method === 'POST') {
    return {
      data: {
        ticket_id: `PX-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-MOCK01`,
        status: "received"
      },
      error: null,
      request_id: "req-mock-contact"
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

export async function createScan(deviceType = "cisco_ios", files = []) {
  const formData = new FormData();
  formData.append("device_type", deviceType || "cisco_ios");

  if (Array.isArray(files)) {
    files.forEach((file) => formData.append("files", file));
  } else if (files) {
    formData.append("files", files);
  }

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

export async function getDevice(scanId, deviceId, _filters = {}) {
  const response = await apiRequest(`/api/scans/${scanId}/devices/${deviceId}`);
  // Normalize response: ensure response.data.device is consistently present
  if (response?.data && !response.data.device) {
    response.data = {
      ...response.data,
      device: response.data,
    };
  }
  return response;
}

export async function getRules(_filters = {}) {
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

export async function downloadCsvReport(scanId) {
  const url = getCsvReportUrl(scanId);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download CSV report: status ${response.status} (${response.statusText || 'Error'})`);
  }
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `scan_${scanId}_report.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function submitContact(data) {
  return apiRequest('/api/contact', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}
