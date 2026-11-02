import torch


class H3SamplingPreset:
    """Pika Flex's released six-step schedule and the user's four-step experiment."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"steps": (["6", "4"], {"default": "6"})}}

    RETURN_TYPES = ("SIGMAS",)
    RETURN_NAMES = ("sigmas",)
    FUNCTION = "build"
    CATEGORY = "video/MinimaxH3"
    DESCRIPTION = "6 = official Pika H3 Flex schedule. 4 = experimental 1000/750/500/250/0 schedule. Video shift 12 is already applied; H3 maps audio to shift 3 internally. Refinement steps are separate."

    def build(self, steps):
        if steps == "6":
            values = [1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0]
        elif steps == "4":
            values = [1.0, 36 / 37, 12 / 13, 0.8, 0.0]
        else:
            raise ValueError("H3 steps must be 4 or 6")
        return (torch.tensor(values, dtype=torch.float32),)


NODE_CLASS_MAPPINGS = {"H3SamplingPreset": H3SamplingPreset}
NODE_DISPLAY_NAME_MAPPINGS = {"H3SamplingPreset": "H3 采样步数 4或6"}


class H3OptionalFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "first": (["使用图片", "空"], {"default": "使用图片"}),
            "last": (["使用图片", "空"], {"default": "使用图片"}),
        }, "optional": {"first_image": ("IMAGE",), "last_image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE", "IMAGE", "COMBO")
    RETURN_NAMES = ("first_frame", "last_frame", "rewriter_task")
    FUNCTION = "select"
    CATEGORY = "video/MinimaxH3"

    def select(self, first, last, first_image=None, last_image=None):
        a = first_image if first == "使用图片" else None
        b = last_image if last == "使用图片" else None
        if first == "使用图片" and a is None:
            raise ValueError("首帧选择了使用图片，请先上传首帧，或选择空")
        if last == "使用图片" and b is None:
            raise ValueError("尾帧选择了使用图片，请先上传尾帧，或选择空")
        task = "FL2AV" if a is not None and b is not None else "I2AV" if a is not None else "L2AV" if b is not None else "T2AV"
        return a, b, task


NODE_CLASS_MAPPINGS["H3OptionalFrames"] = H3OptionalFrames
NODE_DISPLAY_NAME_MAPPINGS["H3OptionalFrames"] = "H3 首尾帧 可选空"


class H3OptionalImage:
    @classmethod
    def INPUT_TYPES(cls):
        import os
        import folder_paths
        root = folder_paths.get_input_directory()
        files = []
        for base, dirs, names in os.walk(root):
            for name in names:
                if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")):
                    files.append(os.path.relpath(os.path.join(base, name), root).replace("\\", "/"))
        return {"required": {"image": (["空"] + sorted(files), {"default": "空", "image_upload": True})}}

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load"
    CATEGORY = "video/MinimaxH3"

    def load(self, image):
        if image == "空":
            return (None,)
        import nodes
        return (nodes.LoadImage().load_image(image)[0],)

    @classmethod
    def IS_CHANGED(cls, image):
        if image == "空":
            return "empty"
        import nodes
        return nodes.LoadImage.IS_CHANGED(image)


class H3FrameTask:
    @classmethod
    def INPUT_TYPES(cls):
        return {"optional": {"first_image": ("IMAGE",), "last_image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE", "IMAGE", "COMBO")
    RETURN_NAMES = ("first_frame", "last_frame", "rewriter_task")
    FUNCTION = "select"
    CATEGORY = "video/MinimaxH3"

    def select(self, first_image=None, last_image=None):
        task = "FL2AV" if first_image is not None and last_image is not None else "I2AV" if first_image is not None else "L2AV" if last_image is not None else "T2AV"
        return first_image, last_image, task


NODE_CLASS_MAPPINGS.update(H3OptionalImage=H3OptionalImage, H3FrameTask=H3FrameTask)
NODE_DISPLAY_NAME_MAPPINGS.update(H3OptionalImage="H3 图片 可选空", H3FrameTask="H3 自动判断首尾帧模式")
