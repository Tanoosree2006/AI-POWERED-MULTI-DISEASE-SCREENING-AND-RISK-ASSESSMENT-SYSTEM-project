"""Transfer-learning classifier: an ImageNet-pretrained ResNet whose last block and head are fine-tuned."""
import torch.nn as nn
import torchvision.models as tvm

ARCHS = {"resnet18": (tvm.resnet18, "ResNet18_Weights"), "resnet50": (tvm.resnet50, "ResNet50_Weights")}


def build_model(arch: str = "resnet18", num_classes: int = 2, pretrained: bool = True, finetune_last_block: bool = True):
    ctor, weights_name = ARCHS[arch]
    weights = getattr(tvm, weights_name).DEFAULT if pretrained else None   # downloads weights on first use
    net = ctor(weights=weights)
    net.fc = nn.Linear(net.fc.in_features, num_classes)
    for name, p in net.named_parameters():
        p.requires_grad = name.startswith("fc") or (finetune_last_block and name.startswith("layer4"))
    return net


def target_layer(net):
    """Last convolutional block: the standard Grad-CAM target for ResNets."""
    return net.layer4
