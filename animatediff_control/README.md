---
license: apache-2.0
library_name: diffusers
---

This checkpoint was converted to Diffusers format by [a-r-r-o-w](https://github.com/a-r-r-o-w/). You can find results and more details adding AnimateDiff SDXL support (beta) to 🤗 Diffusers [here](https://github.com/huggingface/diffusers/pull/6721) The following description is copied from [here](https://huggingface.co/guoyww/animatediff-motion-adapter-v1-5-2).

AnimateDiff is a method that allows you to create videos using pre-existing Stable Diffusion Text to Image models.

It achieves this by inserting motion module layers into a frozen text to image model and training it on video clips to extract a motion prior. These motion modules are applied after the ResNet and Attention blocks in the Stable Diffusion UNet. Their purpose is to introduce coherent motion across image frames. To support these modules we introduce the concepts of a MotionAdapter and UNetMotionModel. These serve as a convenient way to use these motion modules with existing Stable Diffusion models.

Note: The SDXL checkpoint for AnimateDiff is a beta version.

### Usage

```python
import torch
from diffusers import AnimateDiffSDXLPipeline
from diffusers.schedulers import DDIMScheduler, EulerDiscreteScheduler, DEISMultistepScheduler
from diffusers.models import MotionAdapter
from diffusers.utils import export_to_gif

model_id = "stabilityai/stable-diffusion-xl-base-1.0"
adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-sdxl-beta", torch_dtype=torch.float16)
scheduler = DDIMScheduler.from_pretrained(
    model_id,
    subfolder="scheduler",
    clip_sample=False,
    timestep_spacing="linspace",
    beta_schedule="linear",
    steps_offset=1,
)
pipe = AnimateDiffSDXLPipeline.from_pretrained(
    model_id,
    motion_adapter=adapter,
    scheduler=scheduler,
    torch_dtype=torch.float16,
    variant="fp16",
).to("cuda")

# enable memory savings
pipe.enable_vae_slicing()
pipe.enable_vae_tiling()

result = pipe(
    prompt="a panda surfing in the ocean, realistic, hyperrealism, high quality",
    negative_prompt="low quality, worst quality",
    num_inference_steps=20,
    guidance_scale=8,
    width=1024,
    height=1024,
    num_frames=16,
)

export_to_gif(result.frames[0], "animation.gif")
```
