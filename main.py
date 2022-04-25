#!/usr/bin/env python3

import argparse
import tkinter
import tkinter.ttk

from PIL import Image, ImageTk
import numpy as np

from cy.utils import updateLUT


class Application(tkinter.Frame):
    label2color = np.array([
        [  0,   0,   0], # no label(initial state)
        [255,   0,   0], # background
        [  0, 255,   0], # foreground1
        [  0,   0, 255]  # foreground2(not implemented)
    ])

    def __init__(self, img, master=None):
        super().__init__(master)
        self.img = img
        self.master = master
        self.master.title('Nearest Neighbor Segmentation')
        self.resize_ratio = 1.0
        self.label = tkinter.IntVar(value=2) # initialize label to foreground1

        self.pack()
        self.create_widgets()
        self.reset()()


    def create_widgets(self):
        # botton
        self.segmentation_button = tkinter.Button(self, 
            text='Segmentation ON',
            command=self.segmentation())
        self.segmentation_button.grid(row=0, column=1)

        self.reset_button = tkinter.Button(self, 
            text='Reset',
            command=self.reset())
        self.reset_button.grid(row=1, column=1)

        self.label_radio_1 = tkinter.Radiobutton(self,
            text="Background",
            value=1,
            variable=self.label)
        self.label_radio_1.grid(row=2, column=1)

        self.label_radio_2 = tkinter.Radiobutton(self,
            text="Foreground",
            value=2,
            variable=self.label)
        self.label_radio_2.grid(row=3, column=1)

        # canvas
        self.canvas = tkinter.Canvas(self, width=self.img.width, height=self.img.height)
        self.canvas.grid(row=0, column=0, rowspan=4)

        self.canvas.bind("<ButtonPress-1>", self.getPressPoint())
        self.canvas.bind("<Button1-Motion>", self.drawRectangle())
        self.canvas.bind("<ButtonRelease-1>", self.registerLabel())
    
        self.canvas.photo = ImageTk.PhotoImage(self.img)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor='nw', image=self.canvas.photo)


    def segmentation(self):
        def hook():
            if self.segmentation_button.config('text')[-1] == 'Segmentation ON':   
                # show segmentation mask     
                updateLUT(self.dlut, self.tlut)
                r, g, b = np.split(np.array(self.img), 3, axis=2)
                img_label_np = self.tlut[r, g, b][:, :, 0]
                img_segmented_np = np.take(Application.label2color, img_label_np, axis=0).astype(np.uint8)
                img_out = Image.blend(self.img, Image.fromarray(img_segmented_np), 0.5)
                self.segmentation_button.config(text='Segmentation OFF')
            else:
                # show original image
                img_out = self.img
                self.segmentation_button.config(text='Segmentation ON')
            self.canvas.photo = ImageTk.PhotoImage(img_out)
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
                outline="red",
                tag="rect1")  
            self.start_x, self.start_y = event.x, event.y
        return hook


    def drawRectangle(self):
        def hook(event):
            end_x = max(0, min(self.img.width, event.x))
            end_y = max(0, min(self.img.height, event.y))
            self.canvas.coords("rect1", self.start_x, self.start_y, end_x, end_y)
        return hook


    def registerLabel(self):
        def hook(event):
            coords = [
                round(n * self.resize_ratio) for n in self.canvas.coords("rect1")
            ]
            if (coords[2] - coords[0]) * (coords[3] - coords[1]) > 0 and self.label.get() != 0:
                img_crop_np = np.array(self.img.crop(coords), dtype=np.uint8)
                r, g, b = np.split(img_crop_np, 3, axis=2)
                self.dlut[r, g, b] = 0
                self.tlut[r, g, b] = self.label.get()
        return hook


    def reset(self):
        def hook():
            self.label.set(2)
            self.dlut = np.ones((256,256,256), dtype=np.uint16) * 255 * 3  ## initialize max distance
            self.tlut = np.zeros((256,256,256), dtype=np.uint8)
            self.canvas.delete("rect1")
            self.canvas.photo = ImageTk.PhotoImage(self.img)
            self.canvas.itemconfig(self.image_on_canvas, image=self.canvas.photo)
        return hook


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_path')
    args = parser.parse_args()

    original_image = Image.open(args.img_path)

    root = tkinter.Tk()
    app = Application(original_image, master=root)
    app.mainloop()