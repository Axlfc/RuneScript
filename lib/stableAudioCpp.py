import torch
import torchaudio
from einops import rearrange
import argparse
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

class AudioGenerationManager:

    def __init__(self, model_path: str='', device: str='cpu'):
        self.device = device
        if self.device == 'cuda' and (not torch.cuda.is_available()):
            raise ValueError('Requested CUDA device but CUDA is not available.')
        if self.device == 'cuda':
            self.map_location = 'cuda'
        else:
            self.map_location = 'cpu'
        self.model, self.model_config = get_pretrained_model('stabilityai/stable-audio-open-1.0')
        checkpoint = torch.load(model_path, map_location=self.map_location)
        self.model.load_state_dict(checkpoint['model'])
        self.model.to(self.device)
        self.model.eval()
        self.sample_rate = 44100
        self.sample_size = 1024

    def generate_audio_from_text(self, prompt: str, start: int, total: int, output_path: str):
        conditioning = [{'prompt': prompt, 'seconds_start': start, 'seconds_total': total}]
        with torch.no_grad():
            output = generate_diffusion_cond(self.model, steps=100, cfg_scale=7, conditioning=conditioning, sample_size=self.sample_size, sigma_min=0.3, sigma_max=500, sampler_type='dpmpp-3m-sde', device=self.device)
            output = rearrange(output, 'b d n -> d (b n)')
            output = output.to(torch.float32).div(torch.max(torch.abs(output))).clamp(-1, 1).mul(32767).to(torch.int16).cpu()
            torchaudio.save(output_path, output, self.sample_rate)

def main():
    parser = argparse.ArgumentParser(description='Audio Generation using Stable Audio model')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the local .ckpt model file')
    parser.add_argument('--prompt', type=str, required=True, help='Prompt for audio generation')
    parser.add_argument('--start', type=int, required=True, help='Start time in seconds')
    parser.add_argument('--total', type=int, required=True, help='Total time in seconds (max 47)')
    parser.add_argument('--out-dir', type=str, required=True, help='Output directory for the generated audio')
    args = parser.parse_args()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    manager = AudioGenerationManager(model_path=args.model_path, device=device)
    manager.generate_audio_from_text(args.prompt, args.start, args.total, args.out_dir)
if __name__ == '__main__':
    main()