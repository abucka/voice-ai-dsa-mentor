type TranscribeVoiceResponse = {
  text: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

export async function transcribeVoice(audioBase64: string, mimeType: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/help/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audioBase64, mimeType })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to transcribe audio right now.");
  }

  const data = (await response.json()) as TranscribeVoiceResponse;
  return data.text;
}
