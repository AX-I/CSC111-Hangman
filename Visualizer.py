"""An interactive tkinter window.

    - Install/Update PIL (In the case of denied access, install Pillow instead)
    - Install numpy
    - Install tkinter
"""

# Main menu

from tkinter import Frame, Tk, Canvas, N, E, S, W
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import time
from math import sin


f = ('Times', 32, 'bold')


class Coords:
    """Represents coordinates for an element in the GUI

    Instance attributes:
        - pos: The element is centered on these (x, y) coordinates.
        - w2, h2: The radii of the element (1/2 of its dimensions).
        - bounds: The (left, up, right, down) coordinates.
    """
    pos: tuple[int, int]
    w2: int
    h2: int
    bounds: tuple[int, int, int, int]

    def __init__(self, x: int, y: int, w2: int, h2: int) -> None:
        self.pos = (x, y)
        self.w2 = w2
        self.h2 = h2
        self.bounds = (x - w2, y - h2, x + w2, y + h2)


class Project(Frame):
    """Tkinter window for the main menu"""

    def __init__(self, root=None) -> None:
        """Initializes the window"""

        if root is None:
            root = Tk()
        super().__init__(root)

        self.root = root
        self.root.title('CSC111 Project')
        self.W = 960
        self.H = 600

        self.totFrames = 0
        self.startTime = time.time()

        # Center window
        offsetX = root.winfo_screenwidth()//2 - self.W//2
        offsetY = root.winfo_screenheight()//2 - self.H//2
        root.geometry("+{}+{}".format(offsetX, offsetY))
        root.lift()

        self.canvasItems = []

        self.window = 'Menu'

        self.loadMenuAssets()

    def loadMenuAssets(self) -> None:
        """Opens image assets used for main menu"""
        bg = Image.open('Assets/Background.jpg').convert('RGBA')
        self.background = np.array(bg, 'float32')

        title = Image.open('Assets/Title.png')
        self.title = np.array(title, 'float32')

        graphic = Image.open('Assets/Hangman.png').resize((180, 150))
        self.graphic = 255 - np.array(graphic, 'float32')

        light = Image.open('Assets/LightRay.png')
        self.light = np.array(light, 'float32') * 0.6

        letterImgs = {'N': 0, 'V': 0, 'H': 0, 'P': 0}
        letterFile = 'Assets/Letters{}.png'
        for i in letterImgs:
            letterImgs[i] = np.array(Image.open(letterFile.format(i)), 'float32')
            letterImgs[i] *= np.expand_dims(letterImgs[i][:,:,3] / 255, -1)
        self.letterImgs = letterImgs

        self.lettersOffsets = ((np.random.random((8, 2)) - 0.5) * 400).astype('int')

        names = Image.open('Assets/Names.png').convert('RGBA').resize((400, 36))
        self.names = np.array(names, 'float32')

        button = Image.open('Assets/Button.png')
        self.button = np.array(button, 'float32')

        # Copy so we can change the intensity of each button individually
        self.buttons = [np.array(self.button),
                        np.array(self.button),
                        np.array(self.button),
                        np.array(self.button)]

        dims = (120, 60)
        self.buttonPos = [
            Coords(self.W*2//9, self.H-360, *dims),
            Coords(self.W*2//9, self.H-180, *dims),
            Coords(self.W*7//9, self.H-360, *dims),
            Coords(self.W*7//9, self.H-180, *dims)
            ]

        cursor = Image.open('Assets/Cursor.png').resize((53, 50))
        self.cursor = np.clip(np.array(cursor, 'float32') * 1.8, None, 255)

    def loadSelectionAssets(self) -> None:
        """Opens image assets used in AI selection menu"""
        panel = np.array(Image.open('Assets/Panel.png'), 'float32')
        title = np.array(Image.open('Assets/Title_select.png'), 'float32')
        button = np.array(Image.open('Assets/Button2.png').resize((243, 70)), 'float32')
        rect = np.array(Image.open('Assets/Rectangle.png'), 'float32') * 0.4

        bg = np.array(self.background)
        self.blend(bg, title, (self.W//2, self.H//8-40), 'add')
        self.blend(bg, self.light, (self.W//2-80, self.H//2), 'add')
        self.blend(bg, self.light, (self.W//2+50, self.H//2), 'add')
        self.blend(bg, panel, (self.W//2, self.H//2+25), 'alpha')
        self.blend(bg, rect, (self.W*2//3 - 20, self.H*2//5), 'add')
        self.temp_bg = np.clip(bg, 0, 255)

        self.button = np.array(button)
        self.buttons = [np.array(button) for _ in range(5)]

        symbols = np.array(Image.open('Assets/Symbols.png'), 'float32')
        self.symbolImg = symbols
        self.symbols = [
            symbols[60*i:60*(i+1)] for i in range(5)
            ]

        dims = (120, 35)
        self.buttonPos = [
            Coords(self.W*2//7-10, 135 + 90 * i, *dims)
            for i in range(5)
            ]


    def start(self) -> None:
        """Start the rendering loop"""
        self.makeWidgets()
        self.renderMenu()
        self.after(10, self.updateCanvas)

    def makeWidgets(self) -> None:
        """Create the canvas to draw on"""
        self.grid(sticky=N+E+S+W)

        self.d = Canvas(self, width=self.W, height=self.H,
                        highlightthickness=0, highlightbackground='black')
        self.d.grid(row=0, column=0, sticky=N+E+S+W)
        self.d.config(background='#000', cursor='none')
        self.d.bind('<Button-1>', self.clicked)
        self.finalRender = self.d.create_image((self.W/2, self.H/2))


    def renderMenu(self) -> None:
        """Render the main menu"""
        self.totFrames += 1

        # Copy background
        frame = np.array(self.background)

        # Blend in title and names
        self.blend(frame, self.title, (self.W//2, self.H//8), 'add')
        self.blend(frame, self.graphic, (self.W//2, self.H//2), 'add')
        self.blend(frame, self.names, (self.W//2, self.H - 60), 'add')

        # Blend in decorative text
        freq =  (11, 17, 23, 19,  26, 13, 12, 16)
        start = (-8, 22,  0, -15, 18, -3, 16, -4)
        pos = self.lettersOffsets
        abc = 'NVHP' * 2
        for i in range(len(abc)):
            intensity = max(0, sin((self.totFrames + start[i]) / freq[i]))
            if intensity == 0:
                continue
            img = self.letterImgs[abc[i]] * intensity

            position = (self.W//2 + pos[i][0], self.H//2 + pos[i][1])
            self.blend(frame, img, position, 'add')

        w1 = self.W//2 + int(sin(self.totFrames / 29) * 100) - int(sin(self.totFrames / 17) * 20)
        w2 = self.W//2 - int(sin(self.totFrames / 29) * 100) + int(sin(self.totFrames / 17) * 20)
        self.blend(frame, self.light, (w1, self.H//2), 'add')
        self.blend(frame, self.light, (w2, self.H//2), 'add')

        # Blend in menu buttons
        for i in range(len(self.buttons)):
            self.blend(frame, self.buttons[i], self.buttonPos[i].pos, 'alpha')

        # Blend cursor
        mx = max(0, min(self.W, self.d.winfo_pointerx() - self.d.winfo_rootx()))
        my = max(0, min(self.H, self.d.winfo_pointery() - self.d.winfo_rooty()))
        self.blend(frame, self.cursor, (mx + 20, my + 20), 'alpha')

        # Convert numpy array to image
        frame[:,:,3] = 255
        # See https://github.com/numpy/numpy/issues/14281
        # np.clip(frame, 0, 255, out=frame)
        np.maximum(frame, 0, out=frame)
        np.minimum(frame, 255, out=frame)
        i = Image.fromarray(frame.astype("uint8"))
        self.cf = ImageTk.PhotoImage(i)
        self.d.itemconfigure(self.finalRender, image=self.cf)

        self.clearCanvas()

        # Add text to buttons
        texts = ['Instructions', 'Play!', 'Compare AI', 'Quit']
        self.texts = [self.d.create_text(*self.buttonPos[i].pos,
                                         text=texts[i], fill='#fff', font=f)
                      for i in range(len(self.buttons))]

        self.canvasItems = self.texts

    def renderSelect(self) -> None:
        """Render the AI selection screen"""
        self.totFrames += 1

        frame = np.array(self.temp_bg)

        for i in range(len(self.buttons)):
            px, py = self.buttonPos[i].pos
            self.blend(frame, self.buttons[i], (px, py), 'alpha')
            self.blend(frame, self.symbols[i], (px - 92, py), 'alpha')

        # Blend cursor
        mx = max(0, min(self.W, self.d.winfo_pointerx() - self.d.winfo_rootx()))
        my = max(0, min(self.H, self.d.winfo_pointery() - self.d.winfo_rooty()))
        self.blend(frame, self.cursor, (mx + 20, my + 20), 'alpha')

        np.maximum(frame, 0, out=frame)
        np.minimum(frame, 255, out=frame)
        i = Image.fromarray(frame.astype("uint8"))
        self.cf = ImageTk.PhotoImage(i)
        self.d.itemconfigure(self.finalRender, image=self.cf)

        self.clearCanvas()

        texts = ['RandomPlayer', 'RandomGraphPlayer', 'GraphNextPlayer',
                 'FrequentPlayer', 'Human Player']
        self.texts = [self.d.create_text(self.buttonPos[i].pos[0] - 58,
                                         self.buttonPos[i].pos[1],
                                         text=texts[i], fill='#fff',
                                         anchor=W,
                                         font=('Times', 16 if i == 1 else 18))
                      for i in range(len(self.buttons))]

        self.canvasItems = self.texts


    def updateCanvas(self) -> None:
        x = self.d.winfo_pointerx() - self.d.winfo_rootx()
        y = self.d.winfo_pointery() - self.d.winfo_rooty()

        # Button updating
        for i in range(len(self.buttons)):
            self.updateButton(i, x, y, self.buttonPos[i].bounds)

        # This takes the most time
        if self.window == 'Menu':
            self.renderMenu()
        elif self.window == 'Select':
            self.renderSelect()

        self.after(12, self.updateCanvas)


    def updateButton(self, num, x, y, bounds):
        """Highlight a button if selected"""
        if self.selected(x, y, bounds):
            self.buttons[num] = 1.4 * self.button
        else:
            self.buttons[num] = 1.0 * self.button


    def clicked(self, evt) -> None:
        """Handle click events"""
        print(evt.x, evt.y)
        if self.window == 'Menu':
            if self.selected(evt.x, evt.y, self.buttonPos[0].bounds):
                print("Button 0 pressed")
            if self.selected(evt.x, evt.y, self.buttonPos[1].bounds):
                print("Button 1 pressed")
            if self.selected(evt.x, evt.y, self.buttonPos[2].bounds):
                print("Button 2 pressed")
                self.window = 'Select'
                self.loadSelectionAssets()
            if self.selected(evt.x, evt.y, self.buttonPos[3].bounds):
                print("Quit")
                self.root.destroy()


        elif self.window == 'Graph':
            if self.selected(evt.x, evt.y, (100, 480, 380, 550)):
                if self.country == 'C':
                    self.country = 'U'
                else:
                    self.country = 'C'

            if self.selected(evt.x, evt.y, (500, 480, 780, 550)):
                self.window = "Menu"

                self.clearCanvas()
                self.updateCanvas()

    def clearCanvas(self) -> None:
        """Deletes items in self.canvasItems from the canvas self.d"""
        for i in self.canvasItems:
            self.d.delete(i)

    def selected(self, x, y, bounds) -> bool:
        """Return if (x,y) is inside bounds
            bounds = (left, up, right, down)
        """
        return bounds[0] < x < bounds[2] and bounds[1] < y < bounds[3]

    def blend(self, dest: np.array, source: np.array,
              coords: tuple, method="alpha") -> None:
        """Blend image source onto dest, centered at coords (x, y)

        Preconditions:
            - method in {"alpha", "add", "screen"}
        """
        left = coords[0] - (source.shape[1]//2)
        right = left + source.shape[1]
        up = coords[1] - (source.shape[0]//2)
        down = up + source.shape[0]

        src_up = 0
        src_down = source.shape[0]
        src_left = 0
        src_right = source.shape[1]

        # Clip to bounds
        if up < 0:
            src_up -= up
            up = 0
        if left < 0:
            src_left -= left
            left = 0
        if down > self.H:
            src_down -= down - self.H
            down = self.H
        if right > self.W:
            src_right -= right - self.W
            right = self.W

        source = source[src_up:src_down, src_left:src_right]

        if method == 'alpha':
            alpha = np.expand_dims(source[:,:,3], -1) / 255
            np.minimum(alpha, 1, out=alpha)
            dest[up:down, left:right] *= 1 - alpha
            dest[up:down, left:right] += source * alpha

        if method == 'add':
            dest[up:down, left:right] += source

        if method == 'screen':
            dest[up:down, left:right] = 255 - (255 - dest[up:down, left:right]) \
                                        * (255 - source) / 255


if __name__ == "__main__":
    a = Project()
    a.start()
    a.mainloop()
    print("FPS:", a.totFrames / (time.time() - a.startTime))
