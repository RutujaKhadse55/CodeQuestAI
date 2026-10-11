// ─── Offscreen Document — Audio Playback ─────────────────────────────────────
// MV3 service workers cannot play audio. This offscreen document runs in a
// hidden browser context that CAN use Web Audio API / HTMLAudioElement.
// Messages come from the service worker via chrome.runtime.sendMessage.

interface PlayMessage {
  type: "PLAY_TTS";
  audioBase64?: string;   // backend /tts returns base64 audio
  text?: string;          // fallback: use browser SpeechSynthesis
  lang?: string;
}

interface StopMessage {
  type: "STOP_TTS";
}

let currentAudio: HTMLAudioElement | null = null;

chrome.runtime.onMessage.addListener((msg: PlayMessage | StopMessage) => {
  if (msg.type === "STOP_TTS") {
    stopAudio();
    return;
  }

  if (msg.type === "PLAY_TTS") {
    stopAudio();

    // Try base64 audio first (from ElevenLabs via backend)
    if (msg.audioBase64) {
      const audio = new Audio(`data:audio/mpeg;base64,${msg.audioBase64}`);
      audio.onended = () => { currentAudio = null; };
      currentAudio = audio;
      audio.play().catch(() => browserTTSFallback(msg.text ?? "", msg.lang));
    } else {
      // Fallback to browser TTS
      browserTTSFallback(msg.text ?? "", msg.lang);
    }
  }
});

function stopAudio(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  speechSynthesis.cancel();
}

function browserTTSFallback(text: string, lang = "en"): void {
  if (!text) return;
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-US";
  utt.rate = 0.92;
  speechSynthesis.speak(utt);
}
