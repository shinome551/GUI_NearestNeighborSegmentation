#!/usr/bin/env python3

import argparse
import sys
import tkinter
from tkinter import filedialog
import math

from PIL import Image, ImageTk
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms

import cy.utils as cy


class Encoder(nn.Module):
    def __init__(self, in_channels):
        super().__init__()
        self.layer1 = nn.Conv2d(in_channels, 32, 3, 1, 1, bias=False)
        self.layer2 = nn.Conv2d(32, 16, 3, 1, 1, bias=False)
        self.layer3 = nn.Conv2d(16, 3, 3, 1, 1, bias=False)
        self.nonlinear = nn.GELU()

    def forward(self, x):
        x = self.layer1(x)
        x = self.nonlinear(x)
        x = self.layer2(x)
        x = self.nonlinear(x)
        x = self.layer3(x)
        x = torch.sigmoid(x)
        return x


class Pipeline(nn.Module):
    def __init__(self, h, w, in_channels, positional_encoding=True):
        super().__init__()
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.h = h
        self.w = w
        self.in_channels = in_channels
        self.positional_encoding = positional_encoding
        self.initialize()

        if positional_encoding:
            ys = torch.linspace(-1, 1, h)
            xs = torch.linspace(-1, 1, w)
            self.uv = torch.stack(torch.meshgrid(ys, xs), dim=0).unsqueeze(0).to(self.device)


    def initialize(self):
        in_channels = self.in_channels + 2 if self.positional_encoding else self.in_channels
        self.model = Encoder(in_channels).to(self.device)
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
        if self.positional_encoding:
            if coords is not None:
                top = min(coords[1], coords[3])
                bottom = max(coords[1], coords[3])
                left = min(coords[0], coords[2])
                right = max(coords[0], coords[2])
                x = torch.cat([x, self.uv[:, :, top:bottom, left:right]], dim=1)
            else:
                x = torch.cat([x, self.uv], dim=1)
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


class Application(tkinter.Frame):
    label2color = np.array([
        [  0,   0,   0, 255], # background(initial label)
        [255,   0,   0, 128], # foreground1
        [  0,   0, 255, 128]  # foreground2(not implemented)
    ])
    label2colorname = [
        'black', # background(initial label)
        'red', # foreground1
        'blue'  # foreground2(not implemented)
    ]

    def __init__(self, master=None, filename=None):
        super().__init__(master)
        self.master = master
        self.master.title('Nearest Neighbor Segmentation')
        self.resize_ratio = 1.0
        self.history_length = 20

        self.label = tkinter.IntVar(value=1) # initialize label to foreground1
        if filename is None:
            filename = filedialog.askopenfilename()
            if filename == '':
                sys.exit(1)
        img = Image.open(filename)
        self.img = img

        self.pack()
        self.create_widgets()

        w, h = img.size
        self.pipeline = Pipeline(h, w, 3)

        self.reset()()



    def reset(self):
        def hook():
            self.label.set(1)                                              # initialize annotation label to foreground
            self.dlut = np.ones((256,256,256), dtype=np.uint16) * 255 * 3  # initialize dlut to max distance
            self.tlut = np.zeros((256,256,256), dtype=np.uint8)            # initialize tlut to background
            self.mask_toggle_button.config(text='Visualize Mask')
            self.canvas.delete("rect1")
            self.canvas.photo = ImageTk.PhotoImage(self.img)
            self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)
            self.coords_history = []
            self.label_history = []
            self.pipeline.initialize()
        return hook


    def create_widgets(self):
        # botton
        self.mask_toggle_button = tkinter.Button(self, 
            text='Visualize Mask',
            width=10,
            command=self.toggleSegmentationMask())
        self.mask_toggle_button.grid(row=0, column=2)

        self.reset_button = tkinter.Button(self, 
            text='Reset',
            command=self.reset())
        self.reset_button.grid(row=1, column=2)

        self.label_radio_1 = tkinter.Radiobutton(self,
            text='Background',
            foreground='white',
            background=Application.label2colorname[0],
            value=0,
            variable=self.label)
        self.label_radio_1.grid(row=2, column=2)

        self.label_radio_2 = tkinter.Radiobutton(self,
            text='Foreground',
            foreground='white',
            background=Application.label2colorname[1],
            value=1,
            variable=self.label)
        self.label_radio_2.grid(row=3, column=2)

        self.save_button = tkinter.Button(self, 
            text='Save',
            command=self.save())
        self.save_button.grid(row=0, column=0)

        self.load_button = tkinter.Button(self, 
            text='Load',
            command=self.load_and_reset())
        self.load_button.grid(row=1, column=0)

        self.train_button = tkinter.Button(self, 
            text='Train',
            command=self.optimize())
        self.train_button.grid(row=2, column=0)

        # canvas
        self.canvas = tkinter.Canvas(self, width=self.img.width, height=self.img.height)
        self.canvas.grid(row=0, column=1, rowspan=4)

        self.canvas.bind("<ButtonPress-1>", self.getPressPoint())
        self.canvas.bind("<Button1-Motion>", self.drawRectangle())
        self.canvas.bind("<ButtonRelease-1>", self.registerExamplewithLabel())
    
        self.canvas.photo = ImageTk.PhotoImage(self.img)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor='nw', image=self.canvas.photo)


    def toggleSegmentationMask(self):
        def hook():
            if self.mask_toggle_button.config('text')[-1] == 'Visualize Mask': 
                img = self.segmentation()
                self.mask_toggle_button.config(text='Hide Mask')
            else:
                img = self.img
                self.mask_toggle_button.config(text='Visualize Mask')
            self.canvas.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)

        return hook


    def getPressPoint(self):
        def hook(event):
            self.canvas.delete("rect1")
            self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x + 1,
                event.y + 1,
                outline=Application.label2colorname[self.label.get()],
                width=3,
                tag="rect1")  
            self.start_x, self.start_y = event.x, event.y
        return hook


    def drawRectangle(self):
        def hook(event):
            end_x = max(0, min(self.img.width, event.x))
            end_y = max(0, min(self.img.height, event.y))
            self.canvas.coords("rect1", self.start_x, self.start_y, end_x, end_y)
        return hook


    ## order invariant???
    def registerLUT(self, coords, label):
            feature_map = self.pipeline(self.img, coords)
            r, g, b = np.split(feature_map, 3, axis=2)
            self.dlut[r, g, b] = 0
            self.tlut[r, g, b] = label
            cy.updateLUT(self.dlut, self.tlut)


    def registerExamplewithLabel(self):
        def hook(event):
            coords = [
                round(n * self.resize_ratio) for n in self.canvas.coords("rect1")
            ]
            # area check
            if (coords[2] - coords[0]) * (coords[3] - coords[1]) > 0:
                label = self.label.get()
                self.registerLUT(coords, label)
                self.coords_history.append(coords)
                self.label_history.append(label)
                # queue
                if len(self.coords_history) > self.history_length:
                    self.coords_history.pop()
                    self.label_history.pop()

            # segmentation
            if len(np.unique(self.tlut)) > 1:
                img_out = self.segmentation()
                self.canvas.photo = ImageTk.PhotoImage(img_out)
                self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)
                self.mask_toggle_button.config(text='Hide Mask')
        return hook


    def segmentation(self):
        feature_map = self.pipeline(self.img)
        r, g, b = np.split(feature_map, 3, axis=2)
        img_label_np = self.tlut[r, g, b][:, :, 0]
        img_segmented_np = np.take(Application.label2color, img_label_np, axis=0).astype(np.uint8)
        img_mask = Image.fromarray(img_segmented_np[:, :, :3])
        img_alpha = Image.fromarray(img_segmented_np[:, :, 3])
        img_out = Image.composite(self.img, img_mask, img_alpha)
        return img_out
        

    def save(self):
        def hook():
            filename = filedialog.asksaveasfilename(
                title = "Save File as",
                filetypes = [("PNG", ".png"), ("Bitmap", ".bmp"), ("JPEG", ".jpg"), ("Tiff", ".tif") ],
                initialdir = "./",
                initialfile = 'outputs',
                defaultextension = "png"
            )
            if filename != '':
                img_out = self.segmentation()
                img_out.save(filename)
        return hook

    
    def load_and_reset(self):
        def hook():
            filename = filedialog.askopenfilename()
            if filename != '':
                img = Image.open(filename)
                self.img = img
                self.reset()()
        return hook


    def resetLUT(self):
        self.dlut = np.ones((256,256,256), dtype=np.uint16) * 255 * 3  # initialize dlut to max distance
        self.tlut = np.zeros((256,256,256), dtype=np.uint8)            # initialize tlut to background
        for coords, label in zip(self.coords_history, self.label_history):
            self.registerLUT(coords, label)


    def optimize(self):
        def hook():
            self.pipeline.optimize(self.img, self.coords_history, self.label_history)
            self.resetLUT()
            img_out = self.segmentation()
            self.canvas.photo = ImageTk.PhotoImage(img_out)
            self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)

        return hook


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_path')
    args = parser.parse_args()

    root = tkinter.Tk()
    app = Application(master=root, filename=args.img_path)
    root.resizable(width=False, height=False)
    app.mainloop()