"""Grad-CAM (Selvaraju et al., ICCV 2017) implemented with forward hooks.

The heat map is the ReLU of the gradient-weighted sum of the target layer's feature maps. It shows where the MODEL
looked for the chosen class. It is NOT proof that a disease is present or that the model is right.
"""
import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self._acts = None
        self._grads = None
        self._handle = target_layer.register_forward_hook(self._on_forward)

    def _on_forward(self, module, inputs, output):
        self._acts = output.detach()
        output.register_hook(lambda g: setattr(self, "_grads", g.detach()))

    def remove(self):
        self._handle.remove()

    def __call__(self, x: torch.Tensor, class_index: int):
        """x: (N,3,H,W). Returns (cam in [0,1] with shape (N,H,W), softmax probabilities (N,C))."""
        was_training = self.model.training
        self.model.eval()
        x = x.clone().requires_grad_(True)             # keeps the graph alive even if the backbone is frozen
        with torch.enable_grad():
            logits = self.model(x)
            self.model.zero_grad(set_to_none=True)
            logits[:, class_index].sum().backward()
        weights = self._grads.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self._acts).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, size=x.shape[-2:], mode="bilinear", align_corners=False)[:, 0]
        flat = cam.flatten(1)
        lo, hi = flat.min(1)[0][:, None, None], flat.max(1)[0][:, None, None]
        cam = (cam - lo) / (hi - lo + 1e-8)            # all-zero maps stay all-zero
        self.model.train(was_training)
        return cam.detach(), F.softmax(logits.detach(), dim=1)
