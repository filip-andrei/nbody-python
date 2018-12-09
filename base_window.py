import time, datetime
import numpy as np
from PyQt5 import QtOpenGL, QtWidgets, QtCore


class WindowInfo:
    def __init__(self):
        self.size = (0, 0)
        self.mouse = (0, 0)
        self.mouse_down = False
        self.wheel = 0
        self.time = 0
        self.ratio = 1.0
        self.viewport = (0, 0, 0, 0)
        self.keys = np.full(256, False)
        self.old_keys = np.copy(self.keys)

    def key_down(self, key):
        return self.keys[key]

    def key_pressed(self, key):
        return self.keys[key] and not self.old_keys[key]

    def key_released(self, key):
        return not self.keys[key] and self.old_keys[key]


class GLWindow(QtOpenGL.QGLWidget):
    def __init__(self, size, title, out_dir):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSwapInterval(1)
        fmt.setSampleBuffers(True)
        fmt.setDepthBufferSize(24)

        super(GLWindow, self).__init__(fmt, None)
        self.setFixedSize(size[0], size[1])
        self.move(QtWidgets.QDesktopWidget().rect().center() - self.rect().center())
        self.setWindowTitle(title)

        self.start_time = time.clock()
        self.example = lambda: None
        self.ex = None

        self.wnd = WindowInfo()
        self.wnd.viewport = (0, 0) + (size[0] * self.devicePixelRatio(), size[1] * self.devicePixelRatio())
        self.wnd.ratio = size[0] / size[1]
        self.wnd.size = size

        self.out_dir = out_dir

    def keyPressEvent(self, event):
        # Quit when ESC is pressed
        if event.key() == QtCore.Qt.Key_Escape:
            QtCore.QCoreApplication.instance().quit()

        self.wnd.keys[event.nativeVirtualKey() & 0xFF] = True

    def keyReleaseEvent(self, event):
        self.wnd.keys[event.nativeVirtualKey() & 0xFF] = False

    def mousePressEvent(self, event):
        if event.button() == 1:
            self.wnd.mouse_down = True
            self.wnd.mouse = (event.x(), event.y())

    def mouseReleaseEvent(self, event):
        if event.button() == 1:
            self.wnd.mouse_down = False

    def mouseMoveEvent(self, event):
        self.wnd.mouse = (event.x(), event.y())

    def wheelEvent(self, event):
        self.wnd.wheel += event.angleDelta().y()

    def paintGL(self):
        if self.ex is None:
            self.ex = self.example()

        self.wnd.time = time.clock() - self.start_time
        self.ex.render()
        self.wnd.old_keys = np.copy(self.wnd.keys)
        self.wnd.wheel = 0
        self.update()

        if self.out_dir is not None:
            bfr = self.grabFrameBuffer()
            out_path = r"{}\{}.png".format(self.out_dir, datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
            print(out_path)
            bfr.save(out_path)
            QtCore.QCoreApplication.instance().quit()


def run_window(window, out_dir=None):
    app = QtWidgets.QApplication([])
    widget = GLWindow(window.WINDOW_SIZE, getattr(window, 'WINDOW_TITLE', window.__name__), out_dir=out_dir)
    window.wnd = widget.wnd
    widget.example = window
    widget.show()
    app.exec_()
    del app


class Window:
    WINDOW_SIZE = (1280, 720)
    wnd = None  # type: WindowInfo

    def render(self):
        pass
