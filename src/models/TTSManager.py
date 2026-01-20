import queue
import threading
import tempfile
import os
import time
import numpy as np
from lib.dia.dia.model import Dia


class TTSManager:
    def __init__(
            self,
            model_name: str = "nari-labs/Dia-1.6B",
            audio_method: str = "auto",
            device: str | None = None,
            audio_device: str | None = None,
            speed_factor: float = 0.94,  # Speed factor from your screenshot
            voice_pitch: float = 1.0  # New parameter for voice pitch adjustment
    ):
        # Queue for text to synthesize
        self.queue = queue.Queue()
        self.is_playing = False
        self.stopped = False

        # Event to signal when playback finishes
        self.play_finished = threading.Event()
        self.play_finished.set()  # Initially not playing

        # Playback parameters
        self.audio_method = audio_method
        self.audio_device = audio_device
        self.temp_dir = tempfile.gettempdir()
        self.speed_factor = speed_factor
        self.voice_pitch = voice_pitch

        # Choose device: GPU if torch.cuda available
        import torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[TTSManager] Using device: {self.device}")

        # Load the model
        self.model = Dia.from_pretrained(
            model_name,
            compute_dtype="float16",
            device=self.device
        )

        # Model parameters from your screenshot
        # Note: We can't directly pass these to the model as it doesn't support them,
        # but we'll keep them for reference
        self.generation_params = {
            "max_new_tokens": 3072,  # Max tokens
            "cfg_scale": 3.0,  # Guidance strength
            "temperature": 1.3,  # Randomness
            "top_p": 0.95,  # Nucleus sampling
            "cfg_filter_top_k": 30  # CFG filter top k
        }

        self.sample_rate = getattr(self.model, "sample_rate", 24000)
        print(f"[TTSManager] Model loaded with sample_rate={self.sample_rate}")

        # Background thread for queue processing
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def say(self, text: str, priority: bool = False) -> bool:
        """
        Enqueue text for synthesis.
        If priority=True, put it at the front of the queue.
        """
        if not hasattr(self, 'model'):
            print("ERROR: TTS model is not initialized")
            return False

        if priority:
            # Create a temporary queue
            temp_queue = queue.Queue()
            # Add the priority item
            temp_queue.put(text)
            # Transfer existing items to the temp queue
            while not self.queue.empty():
                try:
                    item = self.queue.get_nowait()
                    temp_queue.put(item)
                    self.queue.task_done()
                except queue.Empty:
                    break
            # Replace our queue with the temp queue
            self.queue = temp_queue
        else:
            self.queue.put(text)

        return True

    def stop(self):
        """
        Stop current playback and clear the queue.
        """
        self.stopped = True
        # Empty the queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

        # If sounddevice is available, stop playback
        try:
            import sounddevice as sd
            if self.is_playing:
                sd.stop()
                self.is_playing = False
                self.play_finished.set()
        except ImportError:
            pass

    def _adjust_pitch(self, waveform, factor):
        """
        Adjust the pitch of the waveform without changing duration.
        Uses a simple resampling technique.
        """
        try:
            import librosa
            import soundfile as sf

            # Save to temporary file
            temp_wav = os.path.join(self.temp_dir, f"temp_pitch_{int(time.time())}.wav")
            sf.write(temp_wav, waveform, self.sample_rate)

            # Load with librosa, which can do pitch shifting
            y, sr = librosa.load(temp_wav, sr=self.sample_rate)

            # Pitch shift (positive values raise pitch, negative lower it)
            pitch_shift = 12 * np.log2(factor)  # Convert to semitones
            y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)

            # Clean up
            os.remove(temp_wav)

            return y_shifted
        except ImportError:
            print("[TTSManager] Warning: librosa not available for pitch adjustment")
            return waveform
        except Exception as e:
            print(f"[TTSManager] Error in pitch adjustment: {e}")
            return waveform

    def _adjust_speed(self, waveform, factor):
        """
        Adjust playback speed without affecting pitch.
        """
        try:
            import librosa

            # For speed > 1.0: audio plays faster (shorter)
            # For speed < 1.0: audio plays slower (longer)
            if factor == 1.0:
                return waveform

            # Use librosa's time_stretch
            return librosa.effects.time_stretch(waveform, rate=factor)
        except ImportError:
            # Fall back to simple resampling (affects both speed and pitch)
            print("[TTSManager] Warning: librosa not available for time stretching")
            if factor != 1.0:
                # Resample to change speed
                new_len = int(len(waveform) / factor)
                indices = np.linspace(0, len(waveform) - 1, new_len)
                return np.interp(indices, np.arange(len(waveform)), waveform)
            return waveform
        except Exception as e:
            print(f"[TTSManager] Error in speed adjustment: {e}")
            return waveform

    def _process_queue(self):
        """
        Infinite loop that processes the text queue,
        generates audio with Dia and plays it immediately.
        """
        # Import backends
        try:
            import sounddevice as sd
            SOUNDDEVICE_AVAILABLE = True
        except ImportError:
            SOUNDDEVICE_AVAILABLE = False

        try:
            import soundfile as sf
            SOUNDFILE_AVAILABLE = True
        except ImportError:
            SOUNDFILE_AVAILABLE = False

        try:
            import pygame
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1)
            PYGAME_AVAILABLE = True
        except Exception:
            PYGAME_AVAILABLE = False

        while not self.stopped:
            try:
                # Wait for items in the queue
                text = self.queue.get(timeout=0.5)
                if text is None or self.stopped:
                    self.queue.task_done()
                    break

                # Signal that playback has started
                self.play_finished.clear()
                self.is_playing = True

                print(f"[TTSManager] Generating audio for: {text[:30]}...")
                try:
                    # Generate audio with simple parameters since the model doesn't accept our advanced parameters
                    try:
                        # First try with only use_torch_compile
                        waveform = self.model.generate(
                            text,
                            use_torch_compile=False
                        )
                    except Exception as e:
                        print(f"[TTSManager] Warning: Error with initial generate call: {e}")
                        # Fallback to simplest form
                        try:
                            waveform = self.model.generate(text)
                        except Exception as e2:
                            print(f"[TTSManager] Fatal error in audio generation: {e2}")
                            raise

                    # Convert to numpy
                    if not isinstance(waveform, np.ndarray):
                        if hasattr(waveform, 'numpy'):
                            waveform = waveform.numpy()
                        else:
                            waveform = np.array(waveform)

                    # Apply pitch shift if needed (to fix the deep voice issue)
                    if self.voice_pitch != 1.0:
                        waveform = self._adjust_pitch(waveform, self.voice_pitch)

                    # Apply speed adjustment if needed
                    if self.speed_factor != 1.0:
                        waveform = self._adjust_speed(waveform, self.speed_factor)

                    # Normalize
                    max_val = max(abs(waveform.max()), abs(waveform.min()))
                    if max_val > 1.0:
                        waveform = waveform / max_val

                    # Convert to float32
                    waveform = waveform.astype(np.float32)

                    print(f"[TTSManager] Playing (duration: {len(waveform) / self.sample_rate:.2f}s)")
                    method = self.audio_method
                    if method == "auto":
                        if SOUNDDEVICE_AVAILABLE:
                            method = "sounddevice"
                        elif PYGAME_AVAILABLE:
                            method = "pygame"
                        elif SOUNDFILE_AVAILABLE:
                            method = "file"
                        else:
                            method = "none"

                    # Sounddevice
                    if method == "sounddevice" and SOUNDDEVICE_AVAILABLE:
                        sd.play(waveform, self.sample_rate, device=self.audio_device)
                        sd.wait()  # Block until playback is finished

                    # Pygame
                    elif method == "pygame" and PYGAME_AVAILABLE:
                        temp_wav = os.path.join(self.temp_dir, f"tts_{int(time.time())}.wav")
                        if SOUNDFILE_AVAILABLE:
                            sf.write(temp_wav, waveform, self.sample_rate)
                            pygame.mixer.music.load(temp_wav)
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)
                            os.remove(temp_wav)

                    # File (open with external player)
                    elif method == "file" and SOUNDFILE_AVAILABLE:
                        out_wav = os.path.join(self.temp_dir, f"tts_{int(time.time())}.wav")
                        sf.write(out_wav, waveform, self.sample_rate)
                        import sys
                        if sys.platform.startswith('win'):
                            os.system(f'start {out_wav}')
                        elif sys.platform.startswith('linux'):
                            os.system(f'xdg-open {out_wav}')
                        elif sys.platform.startswith('darwin'):
                            os.system(f'open {out_wav}')
                        time.sleep(len(waveform) / self.sample_rate)

                    else:
                        # No audio method available, just wait the duration of the audio
                        time.sleep(len(waveform) / self.sample_rate)

                except Exception as e:
                    print(f"[TTSManager] Error generating audio: {e}")

                finally:
                    # Mark as complete and signal that it's finished
                    self.is_playing = False
                    self.play_finished.set()
                    self.queue.task_done()

            except queue.Empty:
                continue

        print("[TTSManager] Process stopped")

    def wait_done(self, timeout=None) -> bool:
        """
        Wait for the queue to empty and playback to finish.
        """
        if timeout is None:
            # Wait for empty queue
            if not self.queue.empty():
                try:
                    self.queue.join()
                except:
                    pass

            # Wait for current playback to finish
            self.play_finished.wait()
            return True
        else:
            # With timeout
            start_time = time.time()

            # Wait for empty queue (with timeout)
            while not self.queue.empty():
                if time.time() - start_time > timeout:
                    return False
                time.sleep(0.1)

            # Wait for playback to finish (with remaining timeout)
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                return False

            return self.play_finished.wait(timeout=remaining_time)
