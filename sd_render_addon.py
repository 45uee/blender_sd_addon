bl_info = {
    "name": "Render with Stable Diffusion",
    "blender": (3, 0, 0),
    "category": "Render",
    "description": "Custom render addon with Stable Diffusion integration",
    "location": "View3D > UI > Custom Render",
}

import sys
import os
import cv2
import PIL
import bpy
import numpy as np
import requests
import base64
from bpy.props import IntProperty, StringProperty, FloatProperty

packages_path = sys.path[0]
sys.path.insert(0, packages_path)

output_path = 'your/output/path'


def scene_render(scene, width, height, output_file):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = os.path.join(output_file, "Render.png")
    bpy.ops.render.render(write_still=True)


def sd_img2img(url, prompt, negative_prompt, seed, batch_size, steps, cfg_scale, width, height, denoising_strength,
               output_file):
    with open(os.path.join(output_file, "Render.png"), 'rb') as file:
        image_data = file.read()
    encoded_image = base64.b64encode(image_data).decode('utf-8')

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "batch_size": batch_size,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "denoising_strength": denoising_strength,
        "init_images": [encoded_image],
        "save_images": True
    }

    response = requests.post(url + "/sdapi/v1/img2img", json=payload)
    print(response)
    data = response.json()
    return data['images']


def sd(url, prompt, negative_prompt, seed, batch_size, steps, cfg_scale, width, height, denoising_strength,
       output_file):
    rendered = cv2.imread(os.path.join(output_file, "Render.png"))
    rendered = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)

    imgs = sd_img2img(url, prompt, negative_prompt, seed, batch_size, steps, cfg_scale, width, height,
                      denoising_strength, output_file)

    for base64_string in imgs:
        image_bytes = base64.b64decode(base64_string)
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        cv2.imwrite(os.path.join(output_file, "sd_result.png"), image)
        cv2.imshow("Stable Diffusion", image)
        cv2.imshow("Render", rendered)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class RENDER_OT_CustomRender(bpy.types.Operator):
    bl_idname = "render.custom_render"
    bl_label = "Custom Render"

    def execute(self, context):
        scene = context.scene
        props = scene.render_props
        scene_render(scene, props.width, props.height, props.output_file)
        sd(props.url, props.prompt, props.negative_prompt, props.seed, props.batch_size, props.steps, props.cfg_scale,
           props.width, props.height, props.denoising_strength, props.output_file)
        return {'FINISHED'}


class RENDER_PT_CustomPanel(bpy.types.Panel):
    bl_label = "Render to Stable Diffusion"
    bl_idname = "RENDER_PT_custom_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Custom Render'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.render_props

        layout.prop(props, "width")
        layout.prop(props, "height")
        layout.prop(props, "output_file")
        layout.prop(props, "url")
        layout.prop(props, "batch_size")
        layout.prop(props, "prompt")
        layout.prop(props, "negative_prompt")
        layout.prop(props, "seed")
        layout.prop(props, "steps")
        layout.prop(props, "cfg_scale")
        layout.prop(props, "denoising_strength")

        layout.operator("render.custom_render")


class RenderProperties(bpy.types.PropertyGroup):
    width: IntProperty(
        name="Width",
        description="Width of the rendered image",
        default=512,
        min=1,
    )
    height: IntProperty(
        name="Height",
        description="Height of the rendered image",
        default=512,
        min=1,
    )
    output_file: StringProperty(
        name="Output File",
        description="Path to save the rendered image",
        default=output_path,
    )
    url: StringProperty(
        name="URL",
        description="Stable Diffusion URL",
        default="http://127.0.0.1:8000",
    )
    batch_size: IntProperty(
        name="Batch Size",
        description="Batch size for the API request",
        default=1,
        min=1,
    )
    prompt: StringProperty(
        name="Prompt",
        description="Prompt for Stable Diffusion",
        default="Your positive prompt",
    )
    negative_prompt: StringProperty(
        name="Negative Prompt",
        description="Negative prompt for Stable Diffusion",
        default="Your negative prompt",
    )
    seed: IntProperty(
        name="Seed",
        description="Seed for Stable Diffusion",
        default=-1,
    )
    steps: IntProperty(
        name="Steps",
        description="Steps for Stable Diffusion",
        default=25,
        min=1,
    )
    cfg_scale: FloatProperty(
        name="CFG Scale",
        description="CFG Scale for Stable Diffusion",
        default=7.0,
        min=0.0,
    )
    denoising_strength: FloatProperty(
        name="Denoising Strength",
        description="Denoising strength for Stable Diffusion",
        default=0.7,
        min=0.0,
        max=1.0,
    )


def register():
    bpy.utils.register_class(RENDER_OT_CustomRender)
    bpy.utils.register_class(RENDER_PT_CustomPanel)
    bpy.utils.register_class(RenderProperties)
    bpy.types.Scene.render_props = bpy.props.PointerProperty(type=RenderProperties)


def unregister():
    bpy.utils.unregister_class(RENDER_OT_CustomRender)
    bpy.utils.unregister_class(RENDER_PT_CustomPanel)
    bpy.utils.unregister_class(RenderProperties)
    del bpy.types.Scene.render_props


if __name__ == "__main__":
    register()
