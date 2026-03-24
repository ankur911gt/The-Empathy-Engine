const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function analyzeText(text, emotion = null) {
  const body = { text };
  if (emotion) body.emotion = emotion;

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }

  return data;
}

export { API_BASE };
