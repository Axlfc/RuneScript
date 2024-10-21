import argparse
from typing import Any
from stable_diffusion_cpp import StableDiffusion

class ImageGenerationManager:

    def __init__(self, model_path: str='', vae_path: str='', taesd_path: str='', control_net_path: str='', upscaler_path: str='', lora_model_dir: str='', embed_dir: str='', stacked_id_embed_dir: str='', vae_decode_only: bool=False, vae_tiling: bool=False, free_params_immediately: bool=False, n_threads: int=-1, wtype: str='default', keep_clip_on_cpu: bool=False, keep_control_net_cpu: bool=False, keep_vae_on_cpu: bool=False, verbose: bool=True) -> Any:
        self.model = StableDiffusion(model_path=model_path, vae_path=vae_path, taesd_path=taesd_path, control_net_path=control_net_path, upscaler_path=upscaler_path, lora_model_dir=lora_model_dir, embed_dir=embed_dir, stacked_id_embed_dir=stacked_id_embed_dir, vae_decode_only=vae_decode_only, vae_tiling=vae_tiling, free_params_immediately=free_params_immediately, n_threads=n_threads, wtype=wtype, keep_clip_on_cpu=keep_clip_on_cpu, keep_control_net_cpu=keep_control_net_cpu, keep_vae_on_cpu=keep_vae_on_cpu, verbose=verbose)

    def generate_image_from_text(self, prompt: str, output_path: str):
        images = self.model.txt_to_img(prompt=prompt)
        if images:
            images[0].save(output_path)

def main():
    parser = argparse.ArgumentParser(description='Image Generation using Stable Diffusion model')
    parser.add_argument('--model_path', type=str, help='Path to the model')
    parser.add_argument('--prompt', type=str, help='Prompt for image generation')
    parser.add_argument('--output_path', type=str, help='Output path for the generated image')
    args = parser.parse_args()
    manager = ImageGenerationManager(model_path=args.model_path)
    manager.generate_image_from_text(args.prompt, args.output_path)
if __name__ == '__main__':
    main()