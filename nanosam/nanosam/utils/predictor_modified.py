import onnxruntime
import PIL.Image
import torch
import numpy as np
import torch.nn.functional as F
import nvtx

@nvtx.annotate(message="load_mask_decoder_engine", color="green") # JE
def load_mask_decoder_onnx(path: str):
    """Load the ONNX model for mask decoding.

    Args:
        path (str): Path to the ONNX model file.

    Returns:
        onnxruntime.InferenceSession: ONNX Runtime session for mask decoder.
    """
    return onnxruntime.InferenceSession(path, providers=['CUDAExecutionProvider'])

@nvtx.annotate(message="load_image_encoder_engine", color="green") # JE
def load_image_encoder_onnx(path: str):
    """Load the ONNX model for image encoding.

    Args:
        path (str): Path to the ONNX model file.

    Returns:
        onnxruntime.InferenceSession: ONNX Runtime session for image encoder.
    """
    return onnxruntime.InferenceSession(path, providers=['CUDAExecutionProvider'])

@nvtx.annotate(message="preprocess_image", color="green") # JE
def preprocess_image(image, size: int = 512):

    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)

    image_mean = torch.tensor([123.675, 116.28, 103.53])[:, None, None]
    image_std = torch.tensor([58.395, 57.12, 57.375])[:, None, None]

    image_pil = image
    aspect_ratio = image_pil.width / image_pil.height
    if aspect_ratio >= 1:
        resize_width = size
        resize_height = int(size / aspect_ratio)
    else:
        resize_height = size
        resize_width = int(size * aspect_ratio)

    image_pil_resized = image_pil.resize((resize_width, resize_height))
    image_np_resized = np.asarray(image_pil_resized)
    image_torch_resized = torch.from_numpy(image_np_resized).permute(2, 0, 1)
    image_torch_resized_normalized = (image_torch_resized.float() - image_mean) / image_std
    image_tensor = torch.zeros((1, 3, size, size))
    image_tensor[0, :, :resize_height, :resize_width] = image_torch_resized_normalized

    return image_tensor.cuda()

@nvtx.annotate(message="preprocess_points", color="green") # JE
def preprocess_points(points, image_size, size: int = 1024):
    scale = size / max(*image_size)
    points = points * scale
    return points

@nvtx.annotate(message="upscale_mask", color="green") # JE
def upscale_mask(mask, image_shape, size=256):
    mask = torch.from_numpy(mask)  # Convert NumPy array to PyTorch tensor
    
    if image_shape[1] > image_shape[0]:
        lim_x = size
        lim_y = int(size * image_shape[0] / image_shape[1])
    else:
        lim_x = int(size * image_shape[1] / image_shape[0])
        lim_y = size

    mask = F.interpolate(mask[:, :, :lim_y, :lim_x], image_shape, mode='bilinear')
    
    return mask
    
class Predictor(object):
    """Class for performing inference using ONNX models."""
    @nvtx.annotate(message="Predictor : Initialize Predictor class", color="red") # JE
    def __init__(self,
            image_encoder_onnx: str,
            mask_decoder_onnx: str,
            image_encoder_size: int = 1024,
            orig_image_encoder_size: int = 1024,
        ):
        """Initialize the Predictor with ONNX models.

        Args:
            image_encoder_onnx (str): Path to the ONNX model file for image encoding.
            mask_decoder_onnx (str): Path to the ONNX model file for mask decoding.
            image_encoder_size (int): Size for image encoding.
            orig_image_encoder_size (int): Original size for image encoding.
        """
        self.image_encoder_onnx = load_image_encoder_onnx(image_encoder_onnx)
        self.mask_decoder_onnx = load_mask_decoder_onnx(mask_decoder_onnx)
        self.image_encoder_size = image_encoder_size
        self.orig_image_encoder_size = orig_image_encoder_size
    
    @nvtx.annotate(message="Predictor : Set image", color="red", domain="SetImage") # JE
    def set_image(self, image):
        """Set the input image for inference.

        Args:
            image: Input image.
        """
        self.image = image
        self.image_tensor = preprocess_image(image, self.image_encoder_size)
        # Run the image encoder ONNX model
        nvtx_run_encoder = nvtx.start_range(message="Run image encoder", color="yellow") # JE
        self.features = self.run_onnx_model(self.image_encoder_onnx, self.image_tensor)
        nvtx.end_range(nvtx_run_encoder) # JE
        
    @nvtx.annotate(message="Predictor : Predict", color="red") # JE
    def predict(self, points, point_labels, mask_input=None):
        """Perform inference using the loaded models.

        Args:
            points: Points for inference.
            point_labels: Labels for the points.
            mask_input: Input mask.

        Returns:
            Tuple: Tuple containing the predicted high-resolution mask, IOU predictions,
            and low-resolution mask.
        """
        points = preprocess_points(
            points, 
            (self.image.height, self.image.width),
            self.orig_image_encoder_size
        )
        # Run the mask decoder ONNX model
        mask_iou, low_res_mask = self.run_mask_decoder_onnx(
            self.mask_decoder_onnx,
            self.features,
            points,
            point_labels,
            mask_input
        )

        hi_res_mask = upscale_mask(
            low_res_mask, 
            (self.image.height, self.image.width)                           
        )

        return hi_res_mask, mask_iou, low_res_mask

    @nvtx.annotate(message="run_onnx_model", color="green") # JE
    def run_onnx_model(self, session, input_tensor):
        """Run an ONNX model using ONNX Runtime.

        Args:
            session: ONNX Runtime session.
            input_tensor: Input tensor for the model.

        Returns:
            Output tensor from the model.
        """
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        return session.run([output_name], {input_name: input_tensor.cpu().numpy()})[0]
    
    @nvtx.annotate(message="run_mask_decoder", color="green") # JE
    def run_mask_decoder_onnx(self, mask_decoder_onnx, features, points=None, point_labels=None, mask_input=None):
        if points is not None:
            assert point_labels is not None
            assert len(points) == len(point_labels)

    # Prepare inputs for the ONNX model
        image_point_coords = np.array([points], dtype=np.float32)
        image_point_labels = np.array([point_labels], dtype=np.float32)

        if mask_input is None:
            mask_input = np.zeros((1, 1, 256, 256), dtype=np.float32)
            has_mask_input = np.array([0], dtype=np.float32)
        else:
            has_mask_input = np.array([1], dtype=np.float32)

    # Run the mask decoder ONNX model
        iou_predictions, low_res_masks = mask_decoder_onnx.run(None, {
            "image_embeddings": features,
            "point_coords": image_point_coords,
            "point_labels": image_point_labels,
            "mask_input": mask_input,
            "has_mask_input": has_mask_input
        })

        return iou_predictions, low_res_masks

