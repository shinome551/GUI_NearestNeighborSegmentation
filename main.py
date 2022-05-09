#!/usr/bin/env python3

import argparse
import sys
import tkinter
from tkinter import filedialog
import math

from PIL import Image, ImageTk
import numpy as np

import cy.utils as cy
from pipeline import Pipeline


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
        self.history_length = 20

        if filename is None:
            filename = filedialog.askopenfilename()
            if filename == '':
                sys.exit(1)
        img = Image.open(filename)
        self.img = img
        self.label = tkinter.IntVar(value=1) # initialize label to foreground1

        self.pack()
        self.create_widgets()
        self.reset()()


    def reset(self):
        def hook():
            self.label.set(1)                                              # initialize annotation label to foreground
            self.dlut = np.ones((256,256,256), dtype=np.uint16) * 255 * 3  # initialize dlut to max distance
            self.tlut = np.zeros((256,256,256), dtype=np.uint8)            # initialize tlut to background
            self.mask_toggle_button.config(text='Visualize Mask')
            self.canvas.delete("rect1")
            self.config_canvas(self.img)
            self.coords_history = []
            self.label_history = []
            self.pipeline = Pipeline()
        return hook


    def create_widgets(self):
        # botton
        self.mask_toggle_button = tkinter.Button(self, 
            text='Visualize Mask',
            width=10,
            command=self.toggle_segmentation_mask())
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

        self.canvas.bind("<ButtonPress-1>", self.get_press_point())
        self.canvas.bind("<Button1-Motion>", self.draw_rectangle())
        self.canvas.bind("<ButtonRelease-1>", self.register_example_and_label())
    
        self.config_canvas(self.img)

    
    def config_canvas(self, img):
        self.canvas.photo = ImageTk.PhotoImage(img)
        if hasattr(self, 'image_on_canvas'):
            self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)
        else:
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor='nw', image=self.canvas.photo)


    def toggle_segmentation_mask(self):
        def hook():
            if self.mask_toggle_button.config('text')[-1] == 'Visualize Mask': 
                img = self.segmentation()
                self.mask_toggle_button.config(text='Hide Mask')
            else:
                img = self.img
                self.mask_toggle_button.config(text='Visualize Mask')
            self.config_canvas(img)
        return hook


    def get_press_point(self):
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


    def draw_rectangle(self):
        def hook(event):
            end_x = max(0, min(self.img.width, event.x))
            end_y = max(0, min(self.img.height, event.y))
            self.canvas.coords("rect1", self.start_x, self.start_y, end_x, end_y)
        return hook


    def register_with_LUT(self, coords, label):
        feature_map = self.pipeline(self.img, coords)
        r, g, b = np.split(feature_map, 3, axis=2)
        self.dlut[r, g, b] = 0
        self.tlut[r, g, b] = label
        cy.updateLUT(self.dlut, self.tlut)


    def register_example_and_label(self):
        def hook(event):
            coords = [
                n for n in self.canvas.coords("rect1")
            ]
            # area check
            if (coords[2] - coords[0]) * (coords[3] - coords[1]) > 0:
                label = self.label.get()
                self.register_with_LUT(coords, label)
                # record
                self.coords_history.append(coords)
                self.label_history.append(label)
                # delete old history by FIFO
                if len(self.coords_history) > self.history_length:
                    self.coords_history.pop()
                    self.label_history.pop()

            # segmentation
            if len(np.unique(self.tlut)) > 1:
                img_out = self.segmentation()
                self.config_canvas(img_out)
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


    def register_lut_with_new_model(self):
        self.dlut = np.ones((256,256,256), dtype=np.uint16) * 255 * 3  # initialize dlut to max distance
        self.tlut = np.zeros((256,256,256), dtype=np.uint8)            # initialize tlut to background
        for coords, label in zip(self.coords_history, self.label_history):
            self.register_with_LUT(coords, label)


    def optimize(self):
        def hook():
            self.pipeline.optimize(self.img, self.coords_history, self.label_history)
            self.register_lut_with_new_model()
            img_out = self.segmentation()
            self.config_canvas(img_out)
        return hook


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_path')
    args = parser.parse_args()

    root = tkinter.Tk()
    app = Application(master=root, filename=args.img_path)
    root.resizable(width=False, height=False)
    app.mainloop()