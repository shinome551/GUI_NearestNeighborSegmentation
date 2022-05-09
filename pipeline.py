#!/usr/bin/env python3

import random

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Conv2d(3, 3, kernel_size=3, padding=1, stride=1, bias=False)

    def forward(self, x):
        x = self.layer1(x)
        x = torch.sigmoid(x)
        return x


class Pipeline(nn.Module):
    def __init__(self):
        super().__init__()
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.model = Encoder().to(self.device)
        self.classifier = nn.Linear(3, 2).to(self.device)
        self.optimizer = torch.optim.Adam(
            list(self.model.parameters()) + list(self.classifier.parameters()),
            weight_decay=1e-3
        )


    def _preprocess(self, x, coords=None):
        if coords is not None:
            x = x.crop(coords)
        x = transforms.functional.to_tensor(x)
        x = x.unsqueeze(0).to(self.device)
        return x


    def _postprocess(self, x):
        x = x.cpu().squeeze(0)
        x = x.permute(1, 2, 0)
        x = x.mul(255).byte().numpy()
        return x


    def optimize(self, img, coords_history, label_history, num_step=5):
        self.model.train()
        self.optimizer.zero_grad()
        for i in range(num_step):
            # shuffle
            pair = list(zip(coords_history, label_history))
            random.shuffle(pair)
            coords_history, label_history = zip(*pair)
            for coords, label in zip(coords_history, label_history):
                img_crop = self._preprocess(img, coords=coords).to(self.device)
                target = torch.LongTensor([label]).to(self.device)

                features = self.model(img_crop).mean(dim=(2,3))
                logit = self.classifier(features)
                loss = F.cross_entropy(logit, target) / len(coords_history)
                loss.backward()
            self.optimizer.step()


    # x: PIL image
    def forward(self, x, coords=None):
        x = self._preprocess(x, coords)

        self.model.eval()
        with torch.no_grad():
            x = self.model(x)

        x = self._postprocess(x)
        return x