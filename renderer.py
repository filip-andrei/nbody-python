import moderngl as mgl
import numpy as np
import argparse
import glob
import time
import os
from pyrr import Matrix44
from PyQt5 import QtCore

from base_window import Window, run_window


class Renderer(Window):
    def __init__(self, args):
        self.out_dir = args.out_dir
        self.pointclouds = [args.pointclouds] if "*" not in args.pointclouds else glob.glob(args.pointclouds)
        self.current_pointcloud = 0

        self.ctx = mgl.create_context()

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330 core

                in vec3 in_vert;
                out float opacity;
                uniform mat4 MVP;
                
                float densityAtRadius(float r){
                    return (132820.15f / (2 * 3.14159f * 3160.0f * 3160.0f)) * exp(-r/3160.0f);
                }
                
                void main(){
                    vec4 v = vec4(in_vert, 1.0);
                    gl_Position = MVP * v;
                    opacity = 1.0 - (densityAtRadius(length(vec2(v))) / densityAtRadius(0.0f));
                }
            ''',
            fragment_shader='''
                #version 330 core

                out vec4 color;
                in float opacity;
                
                void main(){
                    color = vec4(0.3, 0.2, 0.7, opacity);
                }
            ''',
        )

        self.mvp = self.prog['MVP']

        vertices = np.load(file=self.pointclouds[0])

        self.vbo = self.ctx.buffer(vertices.astype('f4').tobytes(), dynamic=True)
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

        self.zoom = 1.0
        self.last_mouse_down = False
        self.mouse_pos = (0, 0)
        self.theta = (0, 0)
        self.old_timestamp = 0

        cam_in = "{}\\cam.npy".format(os.getcwd())
        if os.path.isfile(cam_in):
            cam_data = np.load(file=cam_in)
            self.theta = (cam_data[0], cam_data[1])
            self.zoom = cam_data[2]

    def handle_mouse(self):
        if self.wnd.wheel > 0:
            self.zoom *= 1.8
        if self.wnd.wheel < 0:
            self.zoom *= 0.2

        if self.wnd.mouse_down:
            if self.last_mouse_down:
                new_theta = (self.theta[0] + (self.wnd.mouse[0] - self.mouse_pos[0]) * 0.05,
                             self.theta[1] + (self.wnd.mouse[1] - self.mouse_pos[1]) * 0.05)
                self.theta = new_theta

        self.mouse_pos = self.wnd.mouse
        self.last_mouse_down = self.wnd.mouse_down

    def handle_keys(self):
        if self.wnd.key_down(32):
            cam_out = "{}\\cam".format(os.getcwd())
            np.save(arr=np.array([self.theta[0], self.theta[1], self.zoom]), file=cam_out)
            QtCore.QCoreApplication.instance().quit()

    def sleep_to_target_fps(self, target_fps):
        new_timestamp = self.wnd.time
        delta = new_timestamp - self.old_timestamp
        if delta < 1 / target_fps:
            time.sleep(1/target_fps - delta)

        self.old_timestamp = new_timestamp

    def render(self):
        if self.current_pointcloud < len(self.pointclouds):
            self.handle_mouse()
            self.handle_keys()

            self.ctx.viewport = self.wnd.viewport
            self.ctx.clear(0.0, 0.0, 0.0)
            self.ctx.enable(mgl.BLEND)

            vertices = np.load(file=self.pointclouds[self.current_pointcloud])
            self.vbo.write(vertices.astype('f4').tobytes())

            model = Matrix44.from_scale((self.zoom, self.zoom, self.zoom))
            model *= Matrix44.from_x_rotation(-self.theta[1])
            model *= Matrix44.from_y_rotation(-self.theta[0])
            view = Matrix44.look_at((0.0, 0.0, 1.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
            projection = Matrix44.perspective_projection(45.0, self.wnd.ratio, 0.1, 100.0)

            self.mvp.write((projection * view * model).astype('f4').tobytes())
            self.vao.render(mode=mgl.POINTS)

            self.sleep_to_target_fps(60)
            self.current_pointcloud += 1
        else:
            if self.out_dir is None:
                self.current_pointcloud = 0
            else:
                QtCore.QCoreApplication.instance().quit()


parser = argparse.ArgumentParser()
parser.add_argument('--out_dir')
parser.add_argument('pointclouds')

args = parser.parse_args()

run_window(Renderer, args)
