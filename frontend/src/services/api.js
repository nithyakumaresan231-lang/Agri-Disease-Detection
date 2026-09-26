const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Helper to retrieve stored JWT token
 */
export const getToken = () => localStorage.getItem("agri_token");

/**
 * Generic fetch wrapper with automatic JWT authorization header injection
 */
async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.headers || {})
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // If body is not FormData, default to JSON content-type
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  let data;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || "An unexpected error occurred.";
    throw new Error(errorMsg);
  }

  return data;
}

export const authAPI = {
  register: (userData) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData)
    }),

  login: (credentials) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials)
    }),

  getMe: () => request("/auth/me")
};

export const predictionAPI = {
  predict: (formData) =>
    request("/predict", {
      method: "POST",
      body: formData
    })
};

export const historyAPI = {
  getAll: ({ search, crop, status, sort = "desc" } = {}) => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (crop && crop !== "all") params.append("crop", crop);
    if (status && status !== "all") params.append("status", status);
    if (sort) params.append("sort", sort);

    const queryString = params.toString();
    return request(`/history${queryString ? `?${queryString}` : ""}`);
  },

  getById: (id) => request(`/history/${id}`),

  delete: (id) =>
    request(`/history/${id}`, {
      method: "DELETE"
    })
};

export const profileAPI = {
  getProfile: () => request("/profile"),

  updateProfile: (profileData) =>
    request("/profile", {
      method: "PUT",
      body: JSON.stringify(profileData)
    }),

  getStats: () => request("/stats")
};

export { API_BASE_URL };
